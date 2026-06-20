"""Async retry with exponential backoff for transient LLM errors (429 / 5xx).

The Anthropic SDK already retries; this adds an outer, testable layer with a
deterministic backoff schedule and an injectable sleep so unit tests run instant.
"""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")

_RETRYABLE_STATUS = {408, 409, 429, 500, 502, 503, 529}


def is_retryable(exc: BaseException) -> bool:
    """True for transient errors (rate limit / overload / 5xx / connection)."""
    status = getattr(exc, "status_code", None)
    if isinstance(status, int) and status in _RETRYABLE_STATUS:
        return True
    name = type(exc).__name__
    return name in {
        "RateLimitError", "InternalServerError", "APIConnectionError",
        "APITimeoutError", "OverloadedError",
    }


def backoff_delays(retries: int, base: float) -> list[float]:
    """Exponential schedule: base, 2*base, 4*base, …"""
    return [base * (2 ** i) for i in range(retries)]


async def retry_async(
    fn: Callable[[], Awaitable[T]],
    *,
    retries: int = 3,
    base: float = 0.25,
    should_retry: Callable[[BaseException], bool] = is_retryable,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> T:
    """Call `fn`, retrying transient failures with exponential backoff."""
    attempt = 0
    while True:
        try:
            return await fn()
        except BaseException as exc:  # noqa: BLE001 - re-raised unless retryable
            if attempt >= retries or not should_retry(exc):
                raise
            await sleep(base * (2 ** attempt))
            attempt += 1
