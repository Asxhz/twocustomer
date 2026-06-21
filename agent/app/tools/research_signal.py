"""research_product tool — the real, on-demand project signal search.

Takes a project's real identity (terms, handles, repo, discord channel), runs a
live multi-source search (HN, News, Reddit, X/LinkedIn attempt, plus Discord
chatter), persists fresh mentions, synthesizes an insight, and summarizes
sentiment + influence. Everything real; sources with no key/access yield nothing.
"""

from __future__ import annotations

import json

from app.monitor.runner import MonitorState, run_monitor
from app.monitor.scrapers import DEFAULT_SCRAPERS
from app.monitor.insight import synth_insight
from app.monitor.scheduler import persist_mentions

from .registry import registry


async def _influence(brand: str, mentions) -> dict:
    """Sentiment + influence summary over the fresh mentions (best-effort)."""
    if not mentions:
        return {}
    from app.config import get_settings

    s = get_settings()
    by_platform: dict[str, int] = {}
    for m in mentions:
        by_platform[m.platform] = by_platform.get(m.platform, 0) + 1
    top = sorted(mentions, key=lambda m: m.engagement, reverse=True)[:5]
    base = {
        "by_platform": by_platform,
        "top_voices": [{"platform": m.platform, "author": m.author,
                        "engagement": m.engagement, "text": m.text[:160]} for m in top],
    }
    if not s.has_anthropic():
        return base
    try:
        from app.llm.claude import ClaudeLLM
        from app.llm.router import model_for
        from app.fde._json import diagnose_json

        sample = "\n".join(f"- [{m.platform}] {m.text[:160]} ({m.author}, eng {m.engagement})"
                           for m in mentions[:12])
        llm = ClaudeLLM(max_tokens=400, model=model_for("research_synth"))
        data = await diagnose_json(
            llm,
            system=("You analyze brand chatter. Return ONLY JSON: "
                    '{"sentiment": "positive|mixed|negative", '
                    '"themes": ["short theme", ...], '
                    '"influence": "one sentence on who/what is driving the conversation"}'),
            messages=[{"role": "user", "content": f"BRAND: {brand}\n\nMENTIONS:\n{sample}"}],
        )
        base.update(data)
    except Exception:  # noqa: BLE001 - influence is additive, never fatal
        pass
    return base


@registry.tool(
    name="research_product",
    description=(
        "Run a real, live signal search for the current project: search the web, "
        "Reddit, Hacker News, news, X/LinkedIn, and Discord for what people say "
        "about the product, then summarize sentiment, themes, and influence. Use "
        "when the user asks to research / redo a search / find what people think."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "brand_slug": {"type": "string", "description": "The project slug."},
            "terms": {"type": "array", "items": {"type": "string"},
                      "description": "Search terms (brand name, handles, product). Optional."},
            "discord_channel": {"type": "string", "description": "Discord channel id for chatter. Optional."},
        },
        "required": ["brand_slug"],
    },
)
async def research_product(brand_slug: str, terms: list[str] | None = None,
                           discord_channel: str = "") -> str:
    search_terms = terms or [brand_slug.replace("-", " ")]
    result = await run_monitor(terms=search_terms, scrapers=DEFAULT_SCRAPERS,
                               state=MonitorState())

    persisted = 0
    if result.fresh:
        try:
            persisted = await persist_mentions(brand_slug, result.fresh)
        except Exception:  # noqa: BLE001
            persisted = 0

    # Discord chatter as an extra signal surface.
    discord_text = ""
    if discord_channel:
        try:
            from app.channels.discord import read_context

            discord_text = await read_context(discord_channel, limit=20)
        except Exception:  # noqa: BLE001
            discord_text = ""

    insight = await synth_insight(brand_slug, result.high_signal) if result.high_signal else None
    influence = await _influence(brand_slug, result.fresh)

    return json.dumps({
        "kind": "research",
        "brand": brand_slug,
        "fresh": len(result.fresh),
        "high_signal": len(result.high_signal),
        "persisted": persisted,
        "insight": insight,
        "influence": influence,
        "discord_chatter": bool(discord_text),
        "top": [{"platform": m.platform, "text": m.text[:200], "author": m.author,
                 "score": m.score} for m in result.high_signal[:6]],
    }, default=str)
