"""P3.34 + P3.29 — insight synthesis (heuristic) + scheduler build."""

import pytest

from app.monitor.insight import synth_insight
from app.monitor.mention import normalize
from app.monitor.scheduler import build_scheduler, tick


@pytest.mark.asyncio
async def test_synth_empty_is_none():
    assert await synth_insight("aurora", []) is None


def test_heuristic_risk():
    """The deterministic heuristic (used offline, and as the base before Claude
    sharpens it) flags a stockout as risk and leads with the top mention."""
    from app.monitor.insight import _heuristic

    mentions = [
        normalize("x", external_id="1", text="Aurora sold out at Whole Foods again",
                  author="@sam", engagement=500),
        normalize("reddit", external_id="2", text="love aurora", engagement=10),
    ]
    mentions[0].score, mentions[1].score = 0.9, 0.3
    ins = _heuristic("aurora", mentions)
    assert ins["severity"] == "risk"  # 'sold out' -> risk
    assert "sold out" in ins["title"].lower() or "sold out" in ins["body"].lower()


@pytest.mark.asyncio
async def test_synth_returns_insight():
    """synth_insight returns a structured insight (Claude-sharpened when funded,
    heuristic otherwise)."""
    mentions = [normalize("x", external_id="1", text="Aurora sold out again",
                          engagement=500)]
    mentions[0].score = 0.9
    ins = await synth_insight("aurora", mentions)
    assert ins and ins["title"] and ins["body"] and ins["severity"]


def test_build_scheduler_has_job():
    sched = build_scheduler(minutes=15)
    assert sched.get_job("monitor_tick") is not None


@pytest.mark.asyncio
async def test_tick_no_configs_returns_zero():
    # no REGISTERED configs -> nothing to do
    assert await tick() == 0
