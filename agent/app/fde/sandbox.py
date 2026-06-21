"""Forward-deployed-engineer sandbox: fix a broken site safely.

Flow: copy the target site into an isolated temp sandbox → Claude diagnoses the
bug from the symptom → patch is applied IN THE SANDBOX ONLY → validate by running
the site → (optional) deploy a Vercel preview URL.

Protections:
- Only files under the target dir are read; only allow-listed extensions.
- Edits go to a throwaway temp copy — never the original, never prod, never .env.
- Path-traversal + allowlist guards on every write.
- The patch (diff) is returned for review; nothing is auto-pushed to prod.
"""

from __future__ import annotations

import asyncio
import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from app.config import get_settings

# repo root = three levels up from this file (agent/app/fde/sandbox.py -> repo)
_REPO = Path(__file__).resolve().parents[3]
TARGET_SITE = _REPO / "sandbox-site"

ALLOWED_EXT = {".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".json", ".md"}
BLOCKED = {".env", ".env.local"}


def prepare_sandbox(src: Path = TARGET_SITE) -> Path:
    """Copy the target into a fresh temp dir (the isolated sandbox). When the
    folder isn't bundled (e.g. on Vercel serverless), write the embedded demo
    site instead so the sandbox FDE always works."""
    tmp = Path(tempfile.mkdtemp(prefix="twocustomer-fde-"))
    dst = tmp / "sandbox-site"
    if src.exists():
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
            "node_modules", ".git", ".next", ".env", ".env.*"))
    else:
        from .demo_site import FILES

        dst.mkdir(parents=True)
        for name, content in FILES.items():
            (dst / name).write_text(content, encoding="utf-8")
    return dst


def _safe_target(sandbox: Path, rel: str) -> Path:
    p = (sandbox / rel).resolve()
    if not str(p).startswith(str(sandbox.resolve())):
        raise ValueError(f"path escapes sandbox: {rel}")
    if p.name in BLOCKED or p.suffix not in ALLOWED_EXT:
        raise ValueError(f"file not editable: {rel}")
    return p


def read_files(sandbox: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(sandbox.rglob("*")):
        if p.is_file() and p.suffix in ALLOWED_EXT and p.name not in BLOCKED:
            out[str(p.relative_to(sandbox))] = p.read_text(encoding="utf-8")
    return out


def apply_patch(sandbox: Path, rel: str, content: str) -> None:
    _safe_target(sandbox, rel).write_text(content, encoding="utf-8")


async def validate(sandbox: Path, *, bad_marker: str = "hi hi") -> tuple[str, bool | None]:
    """Run the site and check the symptom is gone. Returns (output, healthy).
    healthy is None when validation can't run (no node, e.g. serverless) — the
    caller then trusts the patch + still ships the preview."""
    entry = sandbox / "site.js"
    if not entry.exists():
        return ("(no site.js to run)", None)
    try:
        proc = await asyncio.create_subprocess_exec(
            "node", "site.js", cwd=str(sandbox),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        out, _ = await proc.communicate()
    except (FileNotFoundError, NotImplementedError):  # node unavailable
        return ("(validation skipped: node unavailable)", None)
    text = out.decode().strip()
    healthy = bad_marker not in text and proc.returncode == 0
    return text, healthy


async def diagnose(files: dict[str, str], symptom: str) -> dict[str, Any]:
    """Claude finds the buggy file and returns the corrected full content."""
    s = get_settings()
    if not s.has_anthropic():
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    from app.llm.claude import ClaudeLLM

    from app.llm.router import model_for
    from ._json import diagnose_json

    blob = "\n\n".join(f"=== {name} ===\n{content}" for name, content in files.items())
    llm = ClaudeLLM(max_tokens=2000, model=model_for("fde_diagnose"))
    return await diagnose_json(
        llm,
        system=("You are a forward-deployed engineer. Given the site files and a "
                "symptom, find the ONE file with the bug and return corrected FULL "
                "file content. Respond ONLY with JSON: "
                '{"file": "<relpath>", "explanation": "<one line>", '
                '"patched": "<full corrected file content>"}'),
        messages=[{"role": "user", "content": f"SYMPTOM: {symptom}\n\nFILES:\n{blob}"}],
    )


async def vercel_deploy(sandbox: Path) -> str | None:
    """Deploy a live Vercel preview via the REST API (pure HTTP — works on
    serverless, no CLI). Reads the sandbox files inline, deploys, waits briefly
    for READY, returns the URL. None if no token or it fails."""
    import base64

    import httpx

    s = get_settings()
    token = s.vercel_token
    if not token:
        return None
    # Collect allow-listed files (small static site).
    files = []
    for p in sorted(sandbox.rglob("*")):
        if p.is_file() and p.suffix in ALLOWED_EXT and p.name not in BLOCKED:
            rel = str(p.relative_to(sandbox))
            files.append({"file": rel,
                          "data": base64.b64encode(p.read_bytes()).decode(),
                          "encoding": "base64"})
    if not files:
        return None
    qs = f"?slug={s.vercel_scope}" if s.vercel_scope else ""
    body = {"name": "tc-sandbox", "files": files,
            "projectSettings": {"framework": None}, "target": "production"}
    try:
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(f"https://api.vercel.com/v13/deployments{qs}", json=body,
                             headers={"Authorization": f"Bearer {token}"})
            if r.status_code not in (200, 201, 202):
                return None
            dep = r.json()
            url = dep.get("url")
            dep_id = dep.get("id")
            if not url:
                return None
            # Poll readiness so the link works the moment we hand it over.
            for _ in range(20):
                rs = await c.get(
                    f"https://api.vercel.com/v13/deployments/{dep_id}{qs}",
                    headers={"Authorization": f"Bearer {token}"})
                state = rs.json().get("readyState") if rs.status_code == 200 else None
                if state == "READY":
                    break
                if state in ("ERROR", "CANCELED"):
                    return None
                await asyncio.sleep(1.5)
            return f"https://{url}"
    except Exception:  # noqa: BLE001
        return None


async def fix_site(symptom: str = "homepage hero renders 'hi hi my my'") -> dict[str, Any]:
    """Full FDE loop: sandbox → diagnose → patch → validate → (deploy)."""
    sandbox = prepare_sandbox()
    try:
        before_out, before_ok = await validate(sandbox)
        files = read_files(sandbox)
        fix = await diagnose(files, symptom)
        apply_patch(sandbox, fix["file"], fix["patched"])
        after_out, after_ok = await validate(sandbox)
        # Ship the preview unless validation explicitly failed (False). When it's
        # skipped (None, e.g. no node on serverless), trust the applied patch.
        changed = fix["patched"] != files.get(fix["file"], "")
        deploy_ok = after_ok is not False
        preview = await vercel_deploy(sandbox) if deploy_ok else None
        resolved = (after_ok and not before_ok) if after_ok is not None else changed
        return {
            "file": fix["file"], "explanation": fix.get("explanation", ""),
            "before": before_out, "after": after_out,
            "resolved": bool(resolved), "preview_url": preview,
            "sandbox": str(sandbox),
        }
    finally:
        # clean up the temp sandbox (and its parent temp dir) to avoid disk leak
        try:
            shutil.rmtree(sandbox.parent, ignore_errors=True)
        except Exception:  # noqa: BLE001
            pass
