"""P6.30-6.35 — rate limit, lock, session state (Redis fallback)."""

import pytest

from app.state import limits


@pytest.mark.asyncio
async def test_rate_limit():
    key = "test-rl-user"
    assert await limits.allow(key, limit=2)
    assert await limits.allow(key, limit=2)
    assert not await limits.allow(key, limit=2)  # 3rd blocked


@pytest.mark.asyncio
async def test_lock_mutual_exclusion():
    assert await limits.acquire_lock("brandZ")
    assert not await limits.acquire_lock("brandZ")  # already held
    await limits.release_lock("brandZ")
    assert await limits.acquire_lock("brandZ")  # free again
    await limits.release_lock("brandZ")


@pytest.mark.asyncio
async def test_session_state_roundtrip():
    await limits.session_set("s-123", {"step": 2, "answers": ["a"]})
    got = await limits.session_get("s-123")
    assert got == {"step": 2, "answers": ["a"]}
    assert await limits.session_get("missing") is None
