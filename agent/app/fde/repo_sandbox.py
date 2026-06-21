"""Forward-deployed engineer for a CONNECTED GitHub repo.

Merges the GitHub FDE (read → diagnose → PR) with the sandbox preview: the agent
reads the repo via the API, Claude applies the requested change (a bug fix, a
color/style change, a content edit, …), we open/UPDATE a PR AND build a live
Vercel preview of the patched repo.

Iterative: pass iterate=True to keep editing the SAME working branch + PR, so
follow-up requests ("now make the accent green") stack on the prior change and
redeploy a fresh preview each time — a real "keep editing it" loop.

Reliability contract ("no issues"):
- diff + explanation + PR are produced whenever ANTHROPIC + a token are present.
- The live preview is best-effort via the Vercel REST API; never raises to the
  caller. On total failure it falls back to the bundled sandbox so the user
  ALWAYS gets a live preview URL.
- Returns a `steps` list describing what happened, for live progress UIs.
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

# One stable working branch per repo so iterative edits share a branch + PR.
WORK_BRANCH = "twocustomer-fde"


def _step(steps: list[dict[str, Any]], label: str, **extra: Any) -> None:
    """Append a completed progress step (and optionally attach data)."""
    steps.append({"label": label, "done": True, **extra})


async def _download_tarball(owner: str, repo: str, ref: str | None = None) -> Path | None:
    """Download the repo tarball (optionally at a branch ref) into a temp dir."""
    suffix = f"/{ref}" if ref else ""
    try:
        async with httpx.AsyncClient(timeout=60, headers=github._gh_headers(),
                                     follow_redirects=True) as c:
            r = await c.get(f"{github._API}/repos/{owner}/{repo}/tarball{suffix}")
            if r.status_code != 200:
                return None
            tmp = Path(tempfile.mkdtemp(prefix="twocustomer-repo-"))
            with tarfile.open(fileobj=io.BytesIO(r.content), mode="r:gz") as tf:
                tf.extractall(tmp)  # noqa: S202 - throwaway temp dir
            subdirs = [p for p in tmp.iterdir() if p.is_dir()]
            return subdirs[0] if subdirs else tmp
    except Exception:  # noqa: BLE001
        return None


async def _build_preview(owner: str, repo: str, edits: list[dict[str, str]],
                         ref: str | None = None) -> str | None:
    """Materialize the repo (at `ref` if given) + apply every edit + deploy a
    Vercel preview. Best-effort — returns None on any failure."""
    root = await _download_tarball(owner, repo, ref)
    if root is None:
        return None
    try:
        for e in edits:
            target = (root / e["file"]).resolve()
            if (str(target).startswith(str(root.resolve()))
                    and target.suffix in sandbox.ALLOWED_EXT):
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(e["patched"], encoding="utf-8")
        return await sandbox.vercel_deploy(root)
    except Exception:  # noqa: BLE001
        return None


async def fix_connected_repo(
    repo_url: str, symptom: str, *, context: str = "", token: str = "",
    deploy: bool = True, iterate: bool = False,
) -> dict[str, Any]:
    """Read → diagnose → diff → PR (always) + live preview (best-effort).

    iterate=True reads from the existing working branch (so prior edits persist)
    and pushes onto the same branch/PR — the "keep editing" loop.
    """
    steps: list[dict[str, Any]] = []
    s = get_settings()
    if not s.has_anthropic():
        return {"error": "ANTHROPIC_API_KEY not set — can't diagnose.", "steps": steps}
    repo_url = (repo_url or "").strip() or s.demo_repo  # fall back to the demo repo
    parsed = github.parse_repo(repo_url)
    if not parsed:
        return {"error": "Not a valid public github.com repo URL.", "steps": steps}
    owner, repo = parsed

    reset = github._token_override.set(token) if token else None
    try:
        # 1) Read the connected repo. If we can't, return a clear error. We do NOT
        #    fall back to a bundled site here: that would show the user a different
        #    site than their own, which is confusing. Edit the real code or say why not.
        read_ref = WORK_BRANCH if iterate else None
        try:
            files = await github.read_repo(owner, repo, ref=read_ref)
        except Exception as exc:  # noqa: BLE001
            return {"error": f"Could not read {owner}/{repo} ({exc}). Connect a GitHub "
                             "token with repo access in Settings, then try again.",
                    "steps": steps}
        if not files:
            return {"error": f"No readable source files found in {owner}/{repo}.",
                    "steps": steps}
        _step(steps, f"Read {len(files)} files from {owner}/{repo}"
                     + (f" (branch {WORK_BRANCH})" if iterate else ""))

        # 2) Diagnose the change, with retries — transient JSON/format hiccups
        #    shouldn't surface as a failure or a misleading sandbox preview.
        edits: list[dict[str, str]] = []
        explanation = ""
        for attempt in range(3):
            try:
                fix = await github.diagnose(files, symptom, context)
                edits = fix.get("edits") or []
                explanation = fix.get("explanation", "")
                if edits:
                    break
            except Exception as exc:  # noqa: BLE001
                if attempt == 2:
                    return {"error": f"Couldn't work out that change ({exc}). "
                                     "Rephrase it and I'll retry.", "steps": steps}
        if not edits:
            return {"error": "I read the repo but couldn't pin down that change. "
                             "Try describing it a bit more concretely.", "steps": steps}
        changed = [e["file"] for e in edits]
        _step(steps, f"Diagnosed change · editing {', '.join(changed)}",
              explanation=explanation)

        primary = edits[0]
        before = files.get(primary["file"], "")
        diff = github.unified_diff(before, primary["patched"], primary["file"])

        # 3) Push to the working branch + open/reuse the PR (best-effort).
        #    A fresh (non-iterate) request resets the branch to main first so old
        #    edits don't pile up; iterate=True stacks onto the prior change.
        pushed = await github.push_edits(owner, repo, edits, explanation,
                                         WORK_BRANCH, reset=not iterate)
        pr_url = await github.open_or_reuse_pr(owner, repo, WORK_BRANCH, explanation) \
            if pushed else None
        if pushed:
            _step(steps, "Pushed to branch twocustomer-fde"
                         + (" · PR updated" if pr_url else ""), pr_url=pr_url)

        # 4) Deploy a live preview of the patched tree, with one retry. Read from
        #    the working branch if we pushed; else apply edits to the default tree.
        preview_url = None
        if deploy:
            for _ in range(2):
                preview_url = await _build_preview(
                    owner, repo, edits, ref=WORK_BRANCH if pushed else None)
                if preview_url:
                    break
        if preview_url:
            _step(steps, "Deployed live preview", preview_url=preview_url)
            _step(steps, "Done — open the preview, then ask for the next change")

        if preview_url or pr_url:
            return {
                "repo": f"{owner}/{repo}", "file": primary["file"],
                "files": changed,
                "explanation": explanation,
                "diff": diff[:6000], "pr_url": pr_url,
                "preview_url": preview_url, "resolved": True,
                "branch": WORK_BRANCH, "iterable": True, "steps": steps,
            }
        # Edits computed but neither preview nor PR shipped (no token + deploy
        # failed): return the diff so nothing is lost.
        return {
            "repo": f"{owner}/{repo}", "file": primary["file"], "files": changed,
            "explanation": explanation, "diff": diff[:6000],
            "pr_url": None, "preview_url": None, "resolved": False,
            "preview_note": "Computed the change but couldn't deploy a preview just "
                            "now — try again in a moment.", "steps": steps,
        }
    finally:
        if reset is not None:
            github._token_override.reset(reset)


async def _sandbox_fallback(symptom: str, reason: str,
                            steps: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Always-works fallback: fix the bundled static site and deploy a real live
    preview (no GitHub token / repo build needed). Guarantees a sandbox URL."""
    steps = steps or []
    try:
        from .sandbox import fix_site

        _step(steps, f"Connected repo unavailable ({reason[:80]}) — using sandbox")
        r = await fix_site(symptom)
        if r.get("preview_url"):
            _step(steps, "Deployed live sandbox preview", preview_url=r["preview_url"])
            return {
                "repo": "sandbox", "file": r.get("file", "site.js"),
                "explanation": (r.get("explanation")
                                or "Built a live sandbox preview of the fix."),
                "diff": "", "pr_url": None, "preview_url": r["preview_url"],
                "before": r.get("before"), "after": r.get("after"),
                "resolved": bool(r.get("resolved")), "sandbox_fallback": True,
                "steps": steps,
            }
        return {"error": r.get("error") or reason, "steps": steps}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{reason}; sandbox fallback failed: {exc}", "steps": steps}
