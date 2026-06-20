"""Test fixtures: force the in-memory Redis fallback so unit tests are
deterministic even when live Upstash creds are present in .env. Live Redis is
exercised by scripts/e2e_smoke.py, not the unit suite."""

import pytest


@pytest.fixture(autouse=True, scope="session")
def _disable_sentry():
    """Don't send test errors to Sentry (avoids flush hangs + noise)."""
    try:
        import sentry_sdk

        sentry_sdk.init(dsn="")
    except Exception:  # noqa: BLE001
        pass
    yield


@pytest.fixture(autouse=True)
def _force_redis_fallback(monkeypatch):
    from app.state import redis_client

    rc = redis_client.RedisClient()
    rc._enabled = False  # use the in-process fallback
    rc._fallback = redis_client._MemoryFallback()  # fresh store per test
    monkeypatch.setattr(redis_client, "_client", rc, raising=False)

    # Also force Convex off so convex-backed paths (history, insights) are
    # deterministic in the unit suite even when CONVEX_URL is live.
    from app.state import convex_client

    cc = convex_client.ConvexClient()
    cc._enabled = False
    monkeypatch.setattr(convex_client, "_client", cc, raising=False)

    # Disable the agent shared-token guard in the unit suite (auth is exercised
    # by dedicated tests). Real enforcement happens when AGENT_SHARED_TOKEN is set.
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "shared_token", "", raising=False)
    yield


@pytest.fixture(autouse=True)
def _clean_scheduler_state():
    """Scheduler keeps brand configs/states in module globals. Clear them around
    every test so registrations from one test don't leak into another."""
    from app.monitor import scheduler

    scheduler.REGISTERED.clear()
    scheduler._STATES.clear()
    yield
    scheduler.REGISTERED.clear()
    scheduler._STATES.clear()


@pytest.fixture(autouse=True)
def _offline_llm(request, monkeypatch):
    """Keep the unit suite offline/free: no live Claude calls (stub/heuristic
    paths). Tests marked @pytest.mark.live opt out and use the real key."""
    if not request.node.get_closest_marker("live"):
        from app.config import get_settings

        monkeypatch.setattr(get_settings(), "anthropic_api_key", "", raising=False)
    yield
