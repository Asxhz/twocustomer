"""Conversation history — persisted to Convex `messages`, in-memory when offline.

Lets the agent reload prior turns into context across requests. Convex is the
durable store (realtime + dashboard); the in-memory fallback keeps the agent
working without CONVEX_URL and makes this unit-testable.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from .convex_client import get_convex

# participant -> recent turns (most-recent last)
_MEM: dict[str, deque[dict[str, str]]] = defaultdict(lambda: deque(maxlen=200))


async def append(participant: str, role: str, content: str,
                 *, channel: str = "web") -> None:
    _MEM[participant].append({"role": role, "content": content})
    cx = get_convex()
    if cx.enabled:
        try:
            await cx.mutation("messages:append", participant=participant,
                              role=role, content=content, channel=channel)
        except Exception:  # noqa: BLE001 - persistence best-effort
            pass


async def load(participant: str, *, limit: int = 30) -> list[dict[str, Any]]:
    """Return recent turns as Anthropic-shaped messages (oldest first)."""
    cx = get_convex()
    if cx.enabled:
        try:
            rows = await cx.query("messages:list", participant=participant,
                                  limit=limit)
            if rows:
                # Convex returns newest-first; reverse to chronological.
                return [{"role": r["role"], "content": r["content"]}
                        for r in reversed(rows)]
        except Exception:  # noqa: BLE001
            pass
    return list(_MEM[participant])[-limit:]


def clear(participant: str) -> None:
    _MEM.pop(participant, None)
