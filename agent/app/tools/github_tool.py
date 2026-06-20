"""fix_github — the agent fixes the current software project's GitHub repo.

repo_url + discord_channel come from the project context (injected by the
registry from the run_agent context), so in chat the user just says
"fix the broken checkout" and the agent targets the connected repo.
"""

from __future__ import annotations

from .registry import registry


@registry.tool(
    name="fix_github",
    description=(
        "Diagnose and fix a bug in the current software project's connected "
        "GitHub repo: reads the repo, finds the responsible file, and opens a "
        "pull request (or returns a diff). Use this for a software project when "
        "the user reports something broken."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "symptom": {"type": "string",
                        "description": "What's broken / what to fix."},
        },
        "required": ["symptom"],
    },
)
async def fix_github(symptom: str, repo_url: str = "",
                     discord_channel: str = "") -> str:
    if not repo_url:
        return ("No GitHub repo is connected to this project. Connect one in "
                "onboarding (software project) and try again.")
    # Pull team context from the project's Discord channel, if any.
    context = ""
    try:
        from app.channels import discord

        if discord_channel:
            context = await discord.read_context(discord_channel)
    except Exception:  # noqa: BLE001
        context = ""

    from app.fde.github import fix_github as _run

    res = await _run(repo_url, symptom, context=context)
    if res.get("error"):
        return f"Couldn't fix it: {res['error']}"
    pr = res.get("pr_url")
    tail = f"PR opened: {pr}" if pr else "Diff ready (set GITHUB_TOKEN to open a PR automatically)."
    return (f"Fixed {res.get('repo')} → {res.get('file')}: "
            f"{res.get('explanation')}. {tail}")
