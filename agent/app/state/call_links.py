"""Shared store of FDE preview links produced during a call.

Both the agent (serves them to the web UI) and the voice-control process (records
them when the FDE finishes) use this. Backed by Redis so the two processes share
state; falls back to the in-process Redis stub offline. Keyed by Daily room URL.
"""

from __future__ import annotations

import time
from typing import Any

from .redis_client import get_redis

_TTL = 6 * 3600


def _key(room: str) -> str:
    return f"calllinks:{room}"


async def record_link(room: str, payload: dict[str, Any]) -> None:
    """Append a preview/PR result for a room (most recent last)."""
    if not room:
        return
    r = get_redis()
    cur = await r.get_json(_key(room)) or []
    entry = {
        "preview_url": payload.get("preview_url"),
        "pr_url": payload.get("pr_url"),
        "explanation": payload.get("explanation") or "",
        "files": payload.get("files") or ([payload["file"]] if payload.get("file") else []),
        "at": int(time.time()),
    }
    cur.append(entry)
    await r.set_json(_key(room), cur[-20:], ex=_TTL)


async def get_links(room: str) -> list[dict[str, Any]]:
    if not room:
        return []
    return await get_redis().get_json(_key(room)) or []
