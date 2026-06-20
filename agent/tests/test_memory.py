"""P6.05/P6.13/P6.24 — memory store+recall and cache, on the Redis fallback."""

import pytest

from app.state import memory


@pytest.mark.asyncio
async def test_remember_and_recall():
    b = "aurora-drinks"
    await memory.remember(b, item_id="i1", kind="insight",
                          text="Stockouts at Whole Foods cost ~10% of revenue")
    await memory.remember(b, item_id="i2", kind="insight",
                          text="Yuzu is the breakout SKU on Reddit")
    hits = await memory.recall(b, "why are we losing revenue from stockouts?", k=2)
    assert hits
    assert hits[0].id == "i1"  # stockout item ranks first


@pytest.mark.asyncio
async def test_remember_is_deduped():
    b = "brand-x"
    await memory.remember(b, item_id="dup", kind="insight", text="one")
    await memory.remember(b, item_id="dup", kind="insight", text="one again")
    hits = await memory.recall(b, "one", k=5)
    assert len([h for h in hits if h.id == "dup"]) == 1


@pytest.mark.asyncio
async def test_cache_roundtrip():
    # hermetic: unique key per run so it passes on live Redis or the fallback
    import uuid
    k = memory.cache_key("browserbase", "aurora", uuid.uuid4().hex)
    assert await memory.cache_get(k) is None
    await memory.cache_set(k, {"mentions": 3}, ttl=60)
    assert (await memory.cache_get(k))["mentions"] == 3


@pytest.mark.asyncio
async def test_recall_tool_registered():
    from app.tools import memory_tool  # noqa: F401
    from app.tools.registry import registry

    assert "recall_memory" in registry.names()
