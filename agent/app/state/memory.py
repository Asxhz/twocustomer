"""Agent memory + cache on Redis (Upstash). Redis: Beyond Caching track.

Three capabilities, all over the same Redis:
1. **Memory** — persist insights/campaigns per brand; recall the most relevant
   past items into the agent's context ("beyond caching": the agent cites prior
   findings in new answers).
2. **Semantic recall** — keyword-overlap ranking now; pluggable vector backend
   later (Redis vector index) when an embedding key is available.
3. **Cache** — TTL cache for expensive Browserbase / LLM calls.

Uses the RedisClient, which has an in-process fallback, so this all runs offline
in tests without Upstash configured.
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass
from typing import Any

from .redis_client import get_redis


def _ns_index(brand: str) -> str:
    return f"mem:index:{brand}"


def _ns_item(brand: str, item_id: str) -> str:
    return f"mem:item:{brand}:{item_id}"


@dataclass
class MemoryItem:
    id: str
    kind: str  # insight | campaign
    text: str
    ts: int


async def remember(brand: str, *, item_id: str, kind: str, text: str) -> None:
    """Store a memory item and add it to the brand's index (deduped)."""
    r = get_redis()
    await r.set_json(_ns_item(brand, item_id),
                     {"id": item_id, "kind": kind, "text": text,
                      "ts": int(time.time() * 1000)})
    idx = await r.get_json(_ns_index(brand)) or []
    if item_id not in idx:
        idx.append(item_id)
        await r.set_json(_ns_index(brand), idx)


async def _all_items(brand: str) -> list[MemoryItem]:
    r = get_redis()
    idx = await r.get_json(_ns_index(brand)) or []
    out: list[MemoryItem] = []
    for item_id in idx:
        d = await r.get_json(_ns_item(brand, item_id))
        if d:
            out.append(MemoryItem(id=d["id"], kind=d.get("kind", ""),
                                  text=d.get("text", ""), ts=d.get("ts", 0)))
    return out


def _tokens(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (s or "").lower()))


def _overlap_score(query: str, text: str) -> float:
    q, t = _tokens(query), _tokens(text)
    if not q or not t:
        return 0.0
    return len(q & t) / len(q)


async def recall(brand: str, query: str, *, k: int = 3) -> list[MemoryItem]:
    """Return the top-k past items most relevant to `query` (keyword overlap)."""
    items = await _all_items(brand)
    ranked = sorted(items, key=lambda it: _overlap_score(query, it.text), reverse=True)
    return [it for it in ranked if _overlap_score(query, it.text) > 0][:k]


# ── Cache (beyond just memory) ────────────────────────────────────────────────

def cache_key(*parts: Any) -> str:
    raw = "|".join(str(p) for p in parts)
    return "cache:" + hashlib.sha1(raw.encode()).hexdigest()[:20]


async def cache_get(key: str) -> Any | None:
    return await get_redis().get_json(key)


async def cache_set(key: str, value: Any, ttl: int = 900) -> None:
    await get_redis().set_json(key, value, ex=ttl)
