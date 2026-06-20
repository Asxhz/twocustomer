"""Synthesize an insight from high-signal mentions.

Heuristic offline (cluster by platform, lead with the strongest mention); uses
Claude to write a sharper analyst insight when ANTHROPIC_API_KEY is funded.
Persists to Convex `insights` (no-op offline).
"""

from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.state.convex_client import get_convex

from .mention import Mention


def _heuristic(brand: str, mentions: list[Mention]) -> dict[str, Any]:
    top = max(mentions, key=lambda m: m.score)
    platforms = sorted({m.platform for m in mentions})
    risky = any(w in top.text.lower()
                for w in ("sold out", "broke", "down", "refund", "cancel", "drop"))
    return {
        "title": top.text[:70].strip() or f"Signal spike for {brand}",
        "body": (f"{len(mentions)} high-signal mentions across {', '.join(platforms)}. "
                 f"Leading: \"{top.text[:160]}\" — {top.author}."),
        "severity": "risk" if risky else "opportunity",
    }


async def synth_insight(brand: str, mentions: list[Mention]) -> dict[str, Any] | None:
    if not mentions:
        return None
    insight = _heuristic(brand, mentions)

    s = get_settings()
    if s.has_anthropic():
        try:
            from app.llm.claude import ClaudeLLM

            llm = ClaudeLLM(max_tokens=300)
            sample = "\n".join(f"- [{m.platform}] {m.text[:160]} ({m.author})"
                               for m in mentions[:6])
            resp = await llm.complete(
                system=("You are a brand analyst. From these mentions write ONE "
                        "insight as 'TITLE :: BODY' — title <12 words, body <2 "
                        "sentences with the action implied."),
                messages=[{"role": "user", "content": sample}],
            )
            if "::" in resp.text:
                title, body = resp.text.split("::", 1)
                insight = {"title": title.strip()[:90], "body": body.strip(),
                           "severity": insight["severity"]}
        except Exception:  # noqa: BLE001 - fall back to heuristic
            pass

    cx = get_convex()
    if cx.enabled:
        try:
            await cx.mutation("insights:addInsight", brandId=brand,
                              title=insight["title"], body=insight["body"],
                              severity=insight["severity"])
        except Exception:  # noqa: BLE001
            pass
    return insight
