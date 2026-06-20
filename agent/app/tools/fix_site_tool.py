"""fix_site tool — the FDE loop the agent can call: diagnose a broken site in an
isolated sandbox, patch it, validate, and (optionally) deploy a preview."""

from __future__ import annotations

from app.fde.sandbox import fix_site

from .registry import registry

LAST_FIX: dict[str, dict] = {}


@registry.tool(
    name="fix_site",
    description=(
        "Diagnose and fix a small bug on the brand's site (e.g. the homepage "
        "renders garbled text like 'hi hi my my'). Works in an isolated sandbox "
        "copy — never touches production. Returns the diagnosis, before/after, "
        "and a preview URL when available."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "symptom": {"type": "string",
                        "description": "What's visibly wrong on the site."},
        },
        "required": ["symptom"],
    },
)
async def fix_site_tool(symptom: str) -> str:
    res = await fix_site(symptom)
    LAST_FIX["last"] = res
    status = "✅ fixed" if res["resolved"] else "⚠ not resolved"
    lines = [
        f"{status}: {res['file']} — {res['explanation']}",
        f"  before: {res['before']!r}",
        f"  after:  {res['after']!r}",
    ]
    if res.get("preview_url"):
        lines.append(f"  preview: {res['preview_url']}")
    else:
        lines.append("  (set VERCEL_TOKEN to deploy a live preview URL)")
    return "\n".join(lines)
