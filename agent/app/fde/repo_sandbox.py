"""Forward-deployed engineer for a CONNECTED GitHub repo.

Merges the GitHub FDE (read → diagnose → PR) with the sandbox preview: the agent
reads the repo via the API, Claude finds + patches the buggy file, we open a PR
AND (best-effort) build a live Vercel preview of the patched repo.

Reliability contract ("no issues"):
- diff + explanation + PR are produced whenever ANTHROPIC + a token are present.
- The live preview is best-effort: it needs a build toolchain (vercel CLI) on the
  host. On Vercel serverless it returns None with a clear note (the PR's own
  Vercel integration shows the preview). Never raises to the caller.
"""

from __future__ import annotations

import io
import tarfile
import tempfile
from pathlib import Path
from typing import Any

import httpx

from app.config import get_settings
from . import github, sandbox


async def _download_tarball(owner: str, repo: str) -> Path | None:
    """Download the repo tarball into a temp dir so we can build a preview."""
    try:
        async with httpx.AsyncClient(timeout=60, headers=github._gh_headers(),
                                     follow_redirects=True) as c:
            r = await c.get(f"{github._API}/repos/{owner}/{repo}/tarball")
            if r.status_code != 200:
                return None
            tmp = Path(tempfile.mkdtemp(prefix="twocustomer-repo-"))
            with tarfile.open(fileobj=io.BytesIO(r.content), mode="r:gz") as tf:
                tf.extractall(tmp)  # noqa: S202 - throwaway temp dir
            # tarball extracts to a single top dir
            subdirs = [p for p in tmp.iterdir() if p.is_dir()]
            return subdirs[0] if subdirs else tmp
    except Exception:  # noqa: BLE001
        return None


async def _build_preview(owner: str, repo: str, rel_file: str, patched: str) -> str | None:
    """Materialize the repo + apply the patch + deploy a Vercel preview. Best-effort."""
    root = await _download_tarball(owner, repo)
    if root is None:
        return None
    try:
        target = (root / rel_file).resolve()
        if str(target).startswith(str(root.resolve())) and target.suffix in sandbox.ALLOWED_EXT:
            target.write_text(patched, encoding="utf-8")
        return await sandbox.vercel_deploy(root)
    except Exception:  # noqa: BLE001
        return None


async def fix_connected_repo(
    repo_url: str, symptom: str, *, context: str = "", token: str = "",
    deploy: bool = True,
) -> dict[str, Any]:
    """Read → diagnose → diff → PR (always) + live preview (best-effort)."""
    s = get_settings()
    if not s.has_anthropic():
        return {"error": "ANTHROPIC_API_KEY not set — can't diagnose."}
    parsed = github.parse_repo(repo_url)
    if not parsed:
        return {"error": "Not a valid public github.com repo URL."}
    owner, repo = parsed

    reset = github._token_override.set(token) if token else None
    try:
        files = await github.read_repo(owner, repo)
        if not files:
            return {"error": "No readable source files found in the repo."}
        fix = await github.diagnose(files, symptom, context)
        path = fix["file"]
        before = files.get(path, "")
        after = fix["patched"]
        diff = github.unified_diff(before, after, path)
        branch = f"twocustomer-fix-{abs(hash(symptom)) % 100000}"
        pr_url = await github.open_pr(owner, repo, path, after, fix.get("explanation", ""), branch)

        preview_url = None
        preview_note = ""
        if deploy:
            preview_url = await _build_preview(owner, repo, path, after)
            if not preview_url:
                preview_note = ("Live preview needs a build host (or set VERCEL_TOKEN); "
                                "the PR's Vercel integration also builds a preview.")
        return {
            "repo": f"{owner}/{repo}", "file": path,
            "explanation": fix.get("explanation", ""),
            "diff": diff[:6000], "pr_url": pr_url,
            "preview_url": preview_url, "preview_note": preview_note,
            "resolved": bool(pr_url or after != before),
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
    finally:
        if reset is not None:
            github._token_override.reset(reset)
