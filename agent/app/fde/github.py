"""GitHub-repo forward-deployed engineer.

Founder pastes a public GitHub repo + a symptom (and optional context pulled
from Discord / web monitoring). The agent:
  clone (shallow) -> read source -> Claude diagnoses the one buggy file ->
  patch in the sandbox -> (optional) validate build -> open a PR with the fix
  (when GITHUB_TOKEN is set) or return the diff for review.

Safety: public repos only, shallow clone, size/time caps, allow-listed text
extensions, never pushes to the default branch (PR only), temp sandbox cleaned up.
"""

from __future__ import annotations

import asyncio
import base64
import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

import httpx

from app.config import get_settings

from .sandbox import ALLOWED_EXT, BLOCKED

_GH_RE = re.compile(r"^https?://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?$")
_MAX_FILES = 60
_MAX_BYTES = 400_000  # total source sent to the model
_API = "https://api.github.com"


def parse_repo(url: str) -> tuple[str, str] | None:
    """Return (owner, repo) for a public github.com URL, else None."""
    m = _GH_RE.match((url or "").strip())
    return (m.group(1), m.group(2)) if m else None


async def clone(owner: str, repo: str) -> Path:
    """Shallow-clone a public repo into a temp dir. Raises on failure/timeout."""
    tmp = Path(tempfile.mkdtemp(prefix="twocustomer-gh-"))
    dst = tmp / repo
    proc = await asyncio.create_subprocess_exec(
        "git", "clone", "--depth", "1", "--single-branch",
        f"https://github.com/{owner}/{repo}.git", str(dst),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=90)
    except asyncio.TimeoutError:
        proc.kill()
        shutil.rmtree(tmp, ignore_errors=True)
        raise RuntimeError("clone timed out")
    if proc.returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        raise RuntimeError(f"clone failed: {out.decode()[:200]}")
    return dst


def collect_source(root: Path) -> dict[str, str]:
    """Read allow-listed text files (skipping deps), capped by count + bytes."""
    out: dict[str, str] = {}
    total = 0
    for p in sorted(root.rglob("*")):
        if len(out) >= _MAX_FILES or total >= _MAX_BYTES:
            break
        if not p.is_file() or p.suffix not in ALLOWED_EXT or p.name in BLOCKED:
            continue
        rel = p.relative_to(root)
        if any(part in {"node_modules", ".git", ".next", "dist", "build"}
               for part in rel.parts):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if len(text) > 40_000:  # skip huge files
            continue
        out[str(rel)] = text
        total += len(text)
    return out


async def diagnose(files: dict[str, str], symptom: str, context: str = "") -> dict[str, Any]:
    """Claude finds the buggy file and returns corrected full content."""
    s = get_settings()
    if not s.has_anthropic():
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    from app.llm.claude import ClaudeLLM

    blob = "\n\n".join(f"=== {name} ===\n{content}" for name, content in files.items())
    ctx = f"\n\nADDITIONAL CONTEXT (from Discord / web monitoring):\n{context}" if context else ""
    llm = ClaudeLLM(max_tokens=4000)
    resp = await llm.complete(
        system=("You are a forward-deployed engineer working on a real GitHub repo. "
                "Given the source files, a reported symptom, and any extra context, "
                "find the ONE file most responsible and return the corrected FULL "
                "file content. Make the smallest correct change. Respond ONLY with "
                'JSON: {"file": "<relpath>", "explanation": "<1-2 sentences>", '
                '"patched": "<full corrected file content>"}'),
        messages=[{"role": "user", "content": f"SYMPTOM: {symptom}{ctx}\n\nFILES:\n{blob}"}],
    )
    m = re.search(r"\{.*\}", resp.text, re.DOTALL)
    if not m:
        raise RuntimeError("diagnose: no JSON in model output")
    return json.loads(m.group(0))


def unified_diff(before: str, after: str, path: str) -> str:
    import difflib

    return "".join(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile=f"a/{path}", tofile=f"b/{path}"))


async def open_pr(owner: str, repo: str, path: str, content: str,
                  explanation: str, branch: str) -> str | None:
    """Open a PR with the patched file via the GitHub API. None without a token."""
    s = get_settings()
    if not s.github_token:
        return None
    h = {"Authorization": f"Bearer {s.github_token}",
         "Accept": "application/vnd.github+json"}
    async with httpx.AsyncClient(timeout=30, headers=h) as c:
        meta = (await c.get(f"{_API}/repos/{owner}/{repo}")).json()
        base = meta.get("default_branch", "main")
        base_sha = (await c.get(
            f"{_API}/repos/{owner}/{repo}/git/ref/heads/{base}")).json()["object"]["sha"]
        r = await c.post(f"{_API}/repos/{owner}/{repo}/git/refs",
                         json={"ref": f"refs/heads/{branch}", "sha": base_sha})
        if r.status_code not in (200, 201):
            return None
        cur = await c.get(
            f"{_API}/repos/{owner}/{repo}/contents/{path}", params={"ref": base})
        sha = cur.json().get("sha") if cur.status_code == 200 else None
        body = {"message": f"fix: {explanation[:60]}",
                "content": base64.b64encode(content.encode()).decode(),
                "branch": branch}
        if sha:
            body["sha"] = sha
        up = await c.put(f"{_API}/repos/{owner}/{repo}/contents/{path}", json=body)
        if up.status_code not in (200, 201):
            return None
        pr = await c.post(f"{_API}/repos/{owner}/{repo}/pulls", json={
            "title": f"TwoCustomer fix: {explanation[:60]}",
            "head": branch, "base": base,
            "body": f"Automated fix by TwoCustomer FDE.\n\n{explanation}"})
        return pr.json().get("html_url") if pr.status_code in (200, 201) else None


async def fix_github(repo_url: str, symptom: str, *, context: str = "",
                     branch_suffix: str = "fde") -> dict[str, Any]:
    """Full GitHub FDE loop. Returns the diagnosis, diff, and PR url (if any)."""
    parsed = parse_repo(repo_url)
    if not parsed:
        return {"error": "Not a valid public github.com repo URL."}
    owner, repo = parsed
    sandbox = None
    try:
        sandbox = await clone(owner, repo)
        files = collect_source(sandbox)
        if not files:
            return {"error": "No readable source files found in the repo."}
        fix = await diagnose(files, symptom, context)
        path = fix["file"]
        before = files.get(path, "")
        after = fix["patched"]
        diff = unified_diff(before, after, path)
        branch = f"twocustomer-{branch_suffix}-{abs(hash(symptom)) % 100000}"
        pr_url = await open_pr(owner, repo, path, after, fix.get("explanation", ""), branch)
        return {
            "repo": f"{owner}/{repo}", "file": path,
            "explanation": fix.get("explanation", ""),
            "diff": diff[:6000], "pr_url": pr_url,
            "context_used": bool(context),
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
    finally:
        if sandbox is not None:
            shutil.rmtree(sandbox.parent, ignore_errors=True)
