"""fix_connected_repo — the headline FDE tool.

Given the current project's connected repo + a symptom, diagnose + patch the bug,
open a PR, and build a live preview. Used directly and as the payoff of a video
call ("now fix what we discussed"). Admin-only (gated in main.py).
"""

from __future__ import annotations

from .registry import registry


@registry.tool(
    name="fix_connected_repo",
    description=(
        "Fix a bug in the connected GitHub repo: read the repo, find the broken "
        "file, patch it, open a PR, and build a live preview. Use after the user "
        "describes a concrete symptom (e.g. on a call). Pass repo_url (the "
        "project's repo) and a clear symptom."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "repo_url": {"type": "string", "description": "The project's GitHub repo URL."},
            "symptom": {"type": "string", "description": "What's broken, concretely."},
            "context": {"type": "string", "description": "Optional extra context."},
        },
        "required": ["repo_url", "symptom"],
    },
)
async def fix_connected_repo(repo_url: str, symptom: str, context: str = "") -> str:
    import json

    from app.fde.repo_sandbox import fix_connected_repo as run

    res = await run(repo_url, symptom, context=context)
    return json.dumps(res, default=str)
