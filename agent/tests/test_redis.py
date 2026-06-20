"""P1.39 — redis roundtrip. Uses in-memory fallback when Upstash unset."""

import pytest

from app.state.redis_client import RedisClient


@pytest.mark.asyncio
async def test_set_get_delete_fallback():
    r = RedisClient()
    await r.set("k1", "v1")
    assert await r.get("k1") == "v1"
    await r.delete("k1")
    assert await r.get("k1") is None


@pytest.mark.asyncio
async def test_incr_and_json():
    r = RedisClient()
    # hermetic: clear keys first so this passes on live Redis or the fallback
    await r.delete("counter")
    await r.delete("obj")
    assert await r.incr("counter") == 1
    assert await r.incr("counter") == 2
    await r.set_json("obj", {"a": 1})
    assert await r.get_json("obj") == {"a": 1}


@pytest.mark.asyncio
async def test_ping():
    assert await RedisClient().ping() is True
