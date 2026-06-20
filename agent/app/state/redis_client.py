"""Upstash Redis over its REST API (no TCP, works on serverless/Fluid).

Used for agent memory, vector recall (P6), response cache, rate limits, locks.
Falls back to a no-op in-memory dict when no creds, so tests/offline run.
"""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.config import get_settings


class _MemoryFallback:
    """Tiny in-process store so the agent runs without Upstash configured."""

    def __init__(self) -> None:
        self._d: dict[str, tuple[str, float | None]] = {}

    def _live(self, key: str) -> str | None:
        v = self._d.get(key)
        if v is None:
            return None
        val, exp = v
        if exp is not None and exp < time.time():
            self._d.pop(key, None)
            return None
        return val

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._d[key] = (value, time.time() + ex if ex else None)

    async def get(self, key: str) -> str | None:
        return self._live(key)

    async def delete(self, key: str) -> None:
        self._d.pop(key, None)

    async def incr(self, key: str) -> int:
        cur = int(self._live(key) or "0") + 1
        self._d[key] = (str(cur), None)
        return cur


class RedisClient:
    def __init__(self) -> None:
        s = get_settings()
        self._url = s.upstash_url.rstrip("/")
        self._token = s.upstash_token
        self._enabled = bool(self._url and self._token)
        self._fallback = _MemoryFallback()

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def _cmd(self, *args: Any) -> Any:
        """Run one Upstash REST command via JSON body array -> {"result": ...}.

        Body form (POST base URL with ["CMD","arg",...]) avoids URL-encoding
        issues with arbitrary values.
        """
        if not self._enabled:
            return None
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                self._url,
                headers={"Authorization": f"Bearer {self._token}"},
                json=[str(a) for a in args],
            )
            r.raise_for_status()
            return r.json().get("result")

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        if not self._enabled:
            return await self._fallback.set(key, value, ex)
        if ex:
            await self._cmd("set", key, value, "EX", ex)
        else:
            await self._cmd("set", key, value)

    async def get(self, key: str) -> str | None:
        if not self._enabled:
            return await self._fallback.get(key)
        return await self._cmd("get", key)

    async def delete(self, key: str) -> None:
        if not self._enabled:
            return await self._fallback.delete(key)
        await self._cmd("del", key)

    async def incr(self, key: str) -> int:
        if not self._enabled:
            return await self._fallback.incr(key)
        return int(await self._cmd("incr", key) or 0)

    async def set_json(self, key: str, value: Any, ex: int | None = None) -> None:
        await self.set(key, json.dumps(value, default=str), ex=ex)

    async def get_json(self, key: str) -> Any | None:
        raw = await self.get(key)
        return json.loads(raw) if raw else None

    async def ping(self) -> bool:
        if not self._enabled:
            return True  # fallback always "up"
        return (await self._cmd("ping")) == "PONG"


_client: RedisClient | None = None


def get_redis() -> RedisClient:
    global _client
    if _client is None:
        _client = RedisClient()
    return _client
