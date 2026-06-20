"""P2.34/P2.35 — conversation history persist + load (in-memory fallback)."""

import pytest

from app.state import history


@pytest.mark.asyncio
async def test_append_and_load_chronological():
    p = "user-hist-1"
    history.clear(p)
    await history.append(p, "user", "hello")
    await history.append(p, "assistant", "hi there")
    await history.append(p, "user", "what's leaking revenue?")
    turns = await history.load(p, limit=10)
    assert [t["role"] for t in turns] == ["user", "assistant", "user"]
    assert turns[-1]["content"] == "what's leaking revenue?"


@pytest.mark.asyncio
async def test_load_respects_limit():
    p = "user-hist-2"
    history.clear(p)
    for i in range(10):
        await history.append(p, "user", f"msg {i}")
    turns = await history.load(p, limit=3)
    assert len(turns) == 3
    assert turns[-1]["content"] == "msg 9"


@pytest.mark.asyncio
async def test_load_empty_participant():
    assert await history.load("never-seen") == []
