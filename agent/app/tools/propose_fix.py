"""propose_fix — the bounded-repair / founder-packet engine.

Takes a signal (an insight or anomaly) and produces a structured packet:
summary → evidence → recommended action → a shippable PR/ticket artifact. This
is the forward-deployed-engineer loop: TwoCustomer doesn't just surface the
problem, it hands back something you can ship.

Persists the packet to Convex `packets` (no-op offline). Returns a compact text
summary plus stashes the structured packet for the UI to render.
"""

from __future__ import annotations

import json
import time
from typing import Any

from app.state.convex_client import get_convex

from .registry import registry

# Last packet per brand, so the SSE layer / UI can pick up the structured form.
LAST_PACKET: dict[str, dict[str, Any]] = {}


def _build_packet(brand: str, signal: str, evidence: list[str]) -> dict[str, Any]:
    title = signal.strip().split(".")[0][:80] or "Untitled finding"
    return {
        "brand": brand,
        "title": title,
        "summary": signal.strip(),
        "evidence": evidence or [],
        "recommendedAction": (
            "Investigate the root cause, then apply the smallest reversible fix; "
            "validate against the cited evidence before rollout."
        ),
        "artifact": (
            f"PR/ticket: address '{title}'.\n"
            f"- scope: bounded fix for the cited signal\n"
            f"- validation: re-check the evidence after deploy"
        ),
        "createdAt": int(time.time() * 1000),
    }


@registry.tool(
    name="propose_fix",
    description=(
        "Turn a signal/insight into a founder/CMO packet: summary, evidence, a "
        "recommended action, and a shippable PR/ticket artifact. Use after you've "
        "found a problem worth acting on."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "brand": {"type": "string"},
            "signal": {"type": "string",
                       "description": "The insight/anomaly to act on."},
            "evidence": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["brand", "signal"],
    },
)
async def propose_fix(brand: str, signal: str,
                      evidence: list[str] | None = None) -> str:
    packet = _build_packet(brand, signal, evidence or [])
    LAST_PACKET[brand] = packet

    cx = get_convex()
    if cx.enabled:
        try:
            await cx.mutation(
                "packets:add", brandId=brand, title=packet["title"],
                summary=packet["summary"], evidence=packet["evidence"],
                recommendedAction=packet["recommendedAction"],
                artifact=packet["artifact"],
            )
        except Exception:  # noqa: BLE001 - persistence is best-effort
            pass

    return (f"Packet ready: {packet['title']}\n"
            f"Action: {packet['recommendedAction']}\n"
            f"Artifact:\n{packet['artifact']}")


def last_packet_json(brand: str) -> str:
    return json.dumps(LAST_PACKET.get(brand, {}), default=str)
