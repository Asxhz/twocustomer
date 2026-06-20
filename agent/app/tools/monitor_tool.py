"""monitor_brand tool — runs one monitor pass and reports high-signal mentions.

Lets the Claude agent (and the ASI:One uAgent through it) actually monitor a
brand on demand: scrape → dedup → score → alert.
"""

from __future__ import annotations

from app.monitor.runner import MonitorState, run_monitor
from app.monitor.scrapers import DEFAULT_SCRAPERS

from .registry import registry

# Process-wide monitor state (per-process; persistent dedup lives in Convex).
_STATE = MonitorState()


@registry.tool(
    name="monitor_brand",
    description=(
        "Run a live monitoring pass for a brand: scrape recent mentions, dedup, "
        "score for signal, and return the high-signal ones. Use when asked to "
        "monitor/track a brand or check what people are saying right now."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "terms": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Brand terms / handles to search for.",
            }
        },
        "required": ["terms"],
    },
)
async def monitor_brand(terms: list[str]) -> str:
    result = await run_monitor(
        terms=terms, scrapers=DEFAULT_SCRAPERS, state=_STATE
    )
    if not result.fresh:
        return f"No fresh mentions for {', '.join(terms)} this pass."
    lines = [f"{len(result.fresh)} fresh mentions, "
             f"{len(result.high_signal)} high-signal:"]
    for m in result.high_signal[:5]:
        lines.append(f"- [{m.platform}] {m.text[:120]} (score {m.score})")
    return "\n".join(lines)
