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

import base64
import contextvars
import json
import re
from typing import Any

import httpx

from app.config import get_settings

from .sandbox import ALLOWED_EXT, BLOCKED

_GH_RE = re.compile(r"^https?://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?$")
_MAX_FILES = 60
_MAX_BYTES = 400_000  # total source sent to the model
_API = "https://api.github.com"


# Per-request token override: the web forwards the company's connected OAuth
# token so PRs are opened under their identity. Falls back to the env token.
_token_override: contextvars.ContextVar[str] = contextvars.ContextVar(
    "gh_token_override", default=""
)


def _gh_headers() -> dict[str, str]:
    h = {"Accept": "application/vnd.github+json", "User-Agent": "twocustomer-fde"}
    tok = _token_override.get() or get_settings().github_token
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


def parse_repo(url: str) -> tuple[str, str] | None:
    """Return (owner, repo) for a public github.com URL, else None."""
    m = _GH_RE.match((url or "").strip())
    return (m.group(1), m.group(2)) if m else None


def _skip_path(path: str) -> bool:
    parts = path.split("/")
    if any(p in {"node_modules", ".git", ".next", "dist", "build", "vendor"} for p in parts):
        return True
    name = parts[-1]
    suffix = "." + name.rsplit(".", 1)[1] if "." in name else ""
    return suffix not in ALLOWED_EXT or name in BLOCKED


async def read_repo(owner: str, repo: str, ref: str | None = None) -> dict[str, str]:
    """Read allow-listed source files via the GitHub API (no git binary needed,
    so it runs on serverless). Capped by file count + total bytes.

    When `ref` (a branch name) is given and exists, read from that branch so
    iterative edits see the prior round's changes; otherwise read the default
    branch."""
    out: dict[str, str] = {}
    async with httpx.AsyncClient(timeout=30, headers=_gh_headers()) as c:
        meta = await c.get(f"{_API}/repos/{owner}/{repo}")
        if meta.status_code != 200:
            raise RuntimeError(f"repo not found ({meta.status_code})")
        branch = meta.json().get("default_branch", "main")
        if ref:
            # Use the working branch only if it actually exists.
            chk = await c.get(f"{_API}/repos/{owner}/{repo}/git/ref/heads/{ref}")
            if chk.status_code == 200:
                branch = ref
        tree = await c.get(f"{_API}/repos/{owner}/{repo}/git/trees/{branch}",
                           params={"recursive": "1"})
        if tree.status_code != 200:
            raise RuntimeError("could not read repo tree")
        blobs = [n for n in tree.json().get("tree", [])
                 if n.get("type") == "blob" and not _skip_path(n["path"])
                 and n.get("size", 0) <= 40_000]
        blobs.sort(key=lambda n: n["path"])
        total = 0
        for n in blobs:
            if len(out) >= _MAX_FILES or total >= _MAX_BYTES:
                break
            blob = await c.get(f"{_API}/repos/{owner}/{repo}/git/blobs/{n['sha']}")
            if blob.status_code != 200:
                continue
            data = blob.json()
            if data.get("encoding") != "base64":
                continue
            try:
                text = base64.b64decode(data["content"]).decode("utf-8")
            except (UnicodeDecodeError, ValueError):
                continue
            out[n["path"]] = text
            total += len(text)
    return out


async def diagnose(files: dict[str, str], symptom: str, context: str = "") -> dict[str, Any]:
    """Claude applies the requested change and returns the edited file(s).

    Handles ANY concrete change request — a bug fix, a visual/style change
    (colors, spacing, copy), a content edit, or a logic change — not only bugs.
    Returns {"explanation": str, "edits": [{"file", "patched"}]}. For backward
    compatibility a single {"file","patched"} response is normalized into edits."""
    s = get_settings()
    if not s.has_anthropic():
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    from app.llm.claude import ClaudeLLM

    from app.llm.router import model_for
    from ._json import diagnose_json

    blob = "\n\n".join(f"=== {name} ===\n{content}" for name, content in files.items())
    ctx = f"\n\nADDITIONAL CONTEXT (from Discord / web monitoring):\n{context}" if context else ""
    llm = ClaudeLLM(max_tokens=8000, model=model_for("fde_diagnose"))
    raw = await diagnose_json(
        llm,
        system=(
            "You are a forward-deployed engineer working on a real GitHub repo. "
            "You are given the source files and a REQUEST. The request may be a bug "
            "fix, a visual/style change (e.g. change colors, spacing, copy), a "
            "content edit, or a logic change. Apply EXACTLY what is requested with "
            "the smallest correct change. Touch as few files as possible (usually "
            "one). Return the FULL corrected content of every file you change — "
            "never a diff or partial file. Preserve everything you are not changing. "
            "Respond ONLY with JSON: "
            '{"explanation": "<1-2 sentences, what you changed and why>", '
            '"edits": [{"file": "<relpath>", "patched": "<full corrected file content>"}]}'
        ),
        messages=[{"role": "user", "content": f"REQUEST: {symptom}{ctx}\n\nFILES:\n{blob}"}],
    )
    return _normalize_edits(raw)


def _normalize_edits(raw: dict[str, Any]) -> dict[str, Any]:
    """Accept either the new {edits:[...]} shape or a legacy {file,patched} one."""
    edits = raw.get("edits")
    if not edits and raw.get("file") and raw.get("patched") is not None:
        edits = [{"file": raw["file"], "patched": raw["patched"]}]
    edits = [e for e in (edits or []) if e.get("file") and e.get("patched") is not None]
    return {"explanation": raw.get("explanation", ""), "edits": edits}


def unified_diff(before: str, after: str, path: str) -> str:
    import difflib

    return "".join(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile=f"a/{path}", tofile=f"b/{path}"))


async def open_pr(owner: str, repo: str, path: str, content: str,
                  explanation: str, branch: str) -> str | None:
    """Backward-compatible single-file wrapper around commit_and_pr."""
    return await commit_and_pr(owner, repo, [{"file": path, "patched": content}],
                               explanation, branch)


async def commit_and_pr(owner: str, repo: str, edits: list[dict[str, str]],
                        explanation: str, branch: str) -> str | None:
    """Commit one or more file edits to `branch` and open (or reuse) a PR.

    Idempotent + iteration-friendly: the branch is created from the default
    branch only if missing; pushing more commits to an existing branch updates
    the open PR automatically, so repeated edits accumulate on ONE branch and
    ONE PR rather than spawning a new branch each time. None without a token."""
    s = get_settings()
    if not s.github_token or not edits:
        return None
    h = {"Authorization": f"Bearer {s.github_token}",
         "Accept": "application/vnd.github+json"}
    async with httpx.AsyncClient(timeout=30, headers=h) as c:
        meta = (await c.get(f"{_API}/repos/{owner}/{repo}")).json()
        base = meta.get("default_branch", "main")
        # Create the working branch off base if it doesn't exist yet.
        ref = await c.get(f"{_API}/repos/{owner}/{repo}/git/ref/heads/{branch}")
        if ref.status_code != 200:
            base_sha = (await c.get(
                f"{_API}/repos/{owner}/{repo}/git/ref/heads/{base}")
            ).json()["object"]["sha"]
            mk = await c.post(f"{_API}/repos/{owner}/{repo}/git/refs",
                              json={"ref": f"refs/heads/{branch}", "sha": base_sha})
            if mk.status_code not in (200, 201):
                return None
        # Write each file on the branch (read current sha on the branch to update).
        for e in edits:
            path, content = e["file"], e["patched"]
            cur = await c.get(f"{_API}/repos/{owner}/{repo}/contents/{path}",
                              params={"ref": branch})
            sha = cur.json().get("sha") if cur.status_code == 200 else None
            body = {"message": f"twocustomer: {explanation[:60] or path}",
                    "content": base64.b64encode(content.encode()).decode(),
                    "branch": branch}
            if sha:
                body["sha"] = sha
            up = await c.put(f"{_API}/repos/{owner}/{repo}/contents/{path}", json=body)
            if up.status_code not in (200, 201):
                return None
        # Reuse an open PR for this branch if one exists; else open a new one.
        existing = await c.get(f"{_API}/repos/{owner}/{repo}/pulls",
                               params={"head": f"{owner}:{branch}", "state": "open"})
        if existing.status_code == 200 and existing.json():
            return existing.json()[0].get("html_url")
        pr = await c.post(f"{_API}/repos/{owner}/{repo}/pulls", json={
            "title": f"TwoCustomer: {explanation[:60]}",
            "head": branch, "base": base,
            "body": f"Automated change by TwoCustomer FDE.\n\n{explanation}"})
        return pr.json().get("html_url") if pr.status_code in (200, 201) else None


async def fix_github(repo_url: str, symptom: str, *, context: str = "",
                     branch_suffix: str = "fde", token: str = "") -> dict[str, Any]:
    """Full GitHub FDE loop. Returns the diagnosis, diff, and PR url (if any).

    `token` (the company's connected OAuth token, forwarded by the web) overrides
    the env GITHUB_TOKEN for this request so the PR is opened under their account.
    """
    parsed = parse_repo(repo_url)
    if not parsed:
        return {"error": "Not a valid public github.com repo URL."}
    owner, repo = parsed
    reset = _token_override.set(token) if token else None
    try:
        files = await read_repo(owner, repo)
        if not files:
            return {"error": "No readable source files found in the repo."}
        fix = await diagnose(files, symptom, context)
        edits = fix["edits"]
        if not edits:
            return {"error": "Could not determine a change to make."}
        primary = edits[0]
        diff = unified_diff(files.get(primary["file"], ""), primary["patched"],
                            primary["file"])
        branch = f"twocustomer-{branch_suffix}"
        pr_url = await commit_and_pr(owner, repo, edits, fix.get("explanation", ""), branch)
        return {
            "repo": f"{owner}/{repo}", "file": primary["file"],
            "files": [e["file"] for e in edits],
            "explanation": fix.get("explanation", ""),
            "diff": diff[:6000], "pr_url": pr_url,
            "context_used": bool(context),
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
    finally:
        if reset is not None:
            _token_override.reset(reset)
