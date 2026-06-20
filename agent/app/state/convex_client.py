"""Convex client over the HTTP API.

Convex exposes /api/mutation, /api/query, /api/action that take
{"path": "file:function", "args": {...}, "format": "json"}. We use httpx so the
agent stays a thin Python service. No-op (returns None / []) when CONVEX_URL
unset so the agent runs offline.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings


class ConvexClient:
    def __init__(self) -> None:
        self._url = get_settings().convex_url.rstrip("/")
        self._enabled = bool(self._url)

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def _call(self, kind: str, path: str, args: dict[str, Any]) -> Any:
        if not self._enabled:
            return None
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                f"{self._url}/api/{kind}",
                json={"path": path, "args": args, "format": "json"},
            )
            r.raise_for_status()
            body = r.json()
            if body.get("status") == "error":
                raise RuntimeError(body.get("errorMessage", "convex error"))
            return body.get("value")

    async def mutation(self, path: str, **args: Any) -> Any:
        return await self._call("mutation", path, args)

    async def query(self, path: str, **args: Any) -> Any:
        return await self._call("query", path, args)

    async def action(self, path: str, **args: Any) -> Any:
        return await self._call("action", path, args)


_client: ConvexClient | None = None


def get_convex() -> ConvexClient:
    global _client
    if _client is None:
        _client = ConvexClient()
    return _client
