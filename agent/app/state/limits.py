"""Redis-backed rate limiting, locks, and session state.

Runs on the RedisClient (real Upstash in prod, in-process fallback offline), so
all of this is deterministic in tests without Upstash configured.
"""

from __future__ import annotations

from typing import Any

from .redis_client import get_redis


# ── Rate limiting ─────────────────────────────────────────────────────────────

async def allow(key: str, *, limit: int, window_s: int = 60) -> bool:
    """Fixed-window rate limit. True if the call is under `limit` this window."""
    r = get_redis()
    bucket = f"rl:{key}"
    n = await r.incr(bucket)
    if n == 1 and r.enabled:
        # set TTL on first hit of the window (best-effort)
        await r.set(bucket, "1", ex=window_s)
    return n <= limit


# ── Distributed lock ──────────────────────────────────────────────────────────

async def acquire_lock(name: str, *, ttl_s: int = 300) -> bool:
    """Best-effort lock so two monitor runs for the same brand don't overlap."""
    r = get_redis()
    key = f"lock:{name}"
    if await r.get(key) is not None:
        return False
    await r.set(key, "1", ex=ttl_s)
    return True


async def release_lock(name: str) -> None:
    await get_redis().delete(f"lock:{name}")


# ── Session state ─────────────────────────────────────────────────────────────

async def session_set(session_id: str, state: dict[str, Any],
                      *, ttl_s: int = 3600) -> None:
    await get_redis().set_json(f"sess:{session_id}", state, ex=ttl_s)


async def session_get(session_id: str) -> dict[str, Any] | None:
    return await get_redis().get_json(f"sess:{session_id}")
