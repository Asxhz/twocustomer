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
        "Make a change to the connected GitHub repo and ship a live preview: read "
        "the repo, apply the request, open/update a PR, and deploy a Vercel "
        "preview. The request can be a bug fix OR a visual change (colors, copy, "
        "layout) OR a content edit. Use after the user describes a concrete change "
        "(e.g. on a call). Set iterate=true for a FOLLOW-UP change so it stacks on "
        "the same branch/PR and redeploys an updated preview."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "repo_url": {"type": "string", "description": "The project's GitHub repo URL (optional; defaults to the connected demo repo)."},
            "symptom": {"type": "string", "description": "The concrete change to make — a bug, a color/style change, or a content edit."},
            "context": {"type": "string", "description": "Optional extra context."},
            "iterate": {"type": "boolean", "description": "True for a follow-up edit that builds on the previous one (same branch/PR)."},
        },
        "required": ["symptom"],
    },
)
async def fix_connected_repo(repo_url: str = "", symptom: str = "", context: str = "",
                             iterate: bool = False) -> str:
    import json

    from app.fde.repo_sandbox import fix_connected_repo as run

    res = await run(repo_url, symptom, context=context, iterate=iterate)
    return json.dumps(res, default=str)
