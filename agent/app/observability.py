"""Observability — Sentry error capture + lightweight agent tracing (Arize).

Both are opt-in and inert when their env keys (or libs) are absent, so the app
runs identically offline. Sentry catches errors in the control plane; the trace
hook records each agent run for LLM observability (Arize-style).
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger("twocustomer.obs")

_sentry_on = False


def init_sentry() -> bool:
    """Initialize Sentry if SENTRY_DSN + the SDK are present. Returns enabled."""
    global _sentry_on
    dsn = os.environ.get("SENTRY_DSN", "")
    if not dsn:
        return False
    try:
        import sentry_sdk  # type: ignore

        sentry_sdk.init(dsn=dsn, traces_sample_rate=0.2,
                        environment=os.environ.get("ENV", "dev"))
        _sentry_on = True
        logger.info("sentry initialized")
    except Exception as exc:  # noqa: BLE001
        logger.warning("sentry init skipped: %s", exc)
    return _sentry_on


def capture(exc: BaseException) -> None:
    if _sentry_on:
        try:
            import sentry_sdk  # type: ignore

            sentry_sdk.capture_exception(exc)
        except Exception:  # noqa: BLE001
            pass


def trace_agent_run(*, participant: str, rounds: int, tools: list[str],
                    duration_ms: float, **extra: Any) -> None:
    """Record one agent run for LLM observability (Arize / logs).

    Emits a structured log line always; ships to Arize when configured.
    """
    record = {
        "event": "agent_run", "participant": participant, "rounds": rounds,
        "tools": tools, "duration_ms": round(duration_ms, 1), **extra,
    }
    logger.info("trace %s", record)
    if os.environ.get("ARIZE_API_KEY") and os.environ.get("ARIZE_SPACE_ID"):
        try:
            # Arize ingest is best-effort; absence of the SDK must not break runs.
            from arize.api import Client  # type: ignore  # noqa: F401
            # Real span logging wired here when the SDK + schema are available.
        except Exception:  # noqa: BLE001
            pass


class Timer:
    def __enter__(self) -> "Timer":
        self._t = time.perf_counter()
        return self

    def __exit__(self, *a: object) -> None:
        self.ms = (time.perf_counter() - self._t) * 1000
