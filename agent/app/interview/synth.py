"""Turn a finished interview into a validated insight + persist the session.

Heuristic offline (the most substantive answer becomes the insight); Claude
writes a sharper one when funded. Persists the session to Convex `sessions`.
"""

from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.state.convex_client import get_convex

from .fsm import Interview


def _heuristic(iv: Interview) -> dict[str, Any]:
    answers = [a for a in iv.customer_answers() if a.strip()]
    lead = max(answers, key=len) if answers else "No substantive answer."
    return {
        "title": f"Interview: {iv.customer}",
        "body": lead[:240],
        "severity": "opportunity",
    }


async def synth_session(iv: Interview, *, channel: str = "voice") -> dict[str, Any]:
    insight = _heuristic(iv)
    s = get_settings()
    if s.has_anthropic() and iv.customer_answers():
        try:
            from app.llm.claude import ClaudeLLM

            llm = ClaudeLLM(max_tokens=200)
            convo = "\n".join(f"{t['role']}: {t['text']}" for t in iv.transcript)
            resp = await llm.complete(
                system=("Summarize this customer interview into ONE validated "
                        "insight the brand can act on. <2 sentences."),
                messages=[{"role": "user", "content": convo}],
            )
            if resp.text:
                insight["body"] = resp.text.strip()
        except Exception:  # noqa: BLE001
            pass

    cx = get_convex()
    if cx.enabled:
        try:
            await cx.mutation(
                "sessions:add", brandId=iv.brand, customer=iv.customer,
                channel=channel, transcript=iv.transcript, status="complete",
            )
        except Exception:  # noqa: BLE001
            pass
    return insight
