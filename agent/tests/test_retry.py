"""P2.30/P2.31 — retry/backoff: retryable classification + schedule + behavior."""

import pytest

from app.llm.retry import backoff_delays, is_retryable, retry_async


class _Err(Exception):
    def __init__(self, status):
        self.status_code = status


def test_is_retryable_status():
    assert is_retryable(_Err(429))
    assert is_retryable(_Err(503))
    assert not is_retryable(_Err(400))
    assert not is_retryable(_Err(401))


def test_is_retryable_by_name():
    class RateLimitError(Exception):
        pass

    assert is_retryable(RateLimitError())
    assert not is_retryable(ValueError())


def test_backoff_schedule():
    assert backoff_delays(3, 0.25) == [0.25, 0.5, 1.0]


@pytest.mark.asyncio
async def test_retry_recovers_after_transient():
    calls = {"n": 0}
    slept: list[float] = []

    async def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise _Err(429)
        return "ok"

    async def fake_sleep(d):
        slept.append(d)

    out = await retry_async(flaky, retries=3, base=0.1, sleep=fake_sleep)
    assert out == "ok"
    assert calls["n"] == 3
    assert slept == [0.1, 0.2]  # two backoffs before success


@pytest.mark.asyncio
async def test_retry_gives_up_on_non_retryable():
    async def boom():
        raise _Err(400)

    with pytest.raises(_Err):
        await retry_async(boom, retries=3, base=0, sleep=lambda d: _noop())


async def _noop():
    return None
