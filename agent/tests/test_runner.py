"""P3.28/P3.36/P3.38 — monitor run: scrape→dedup→score→alert (injected scraper)."""

import pytest

from app.monitor.mention import normalize
from app.monitor.runner import MonitorState, run_monitor


async def _fake_scraper(term: str):
    return [
        normalize("reddit", external_id="a", text=f"{term} is sold out everywhere",
                  engagement=1),
        normalize("reddit", external_id="b", text=f"love {term}", engagement=900),
    ]


@pytest.mark.asyncio
async def test_run_monitor_dedup_score_alert():
    state = MonitorState()
    alerts: list[str] = []

    async def on_alert(m):
        alerts.append(m.external_id)

    res = await run_monitor(terms=["Aurora"], scrapers=[_fake_scraper],
                            state=state, on_alert=on_alert)
    assert len(res.fresh) == 2
    assert res.high_signal  # the engagement=900 one
    assert "b" in alerts

    # Second pass with same ids → nothing fresh, no new alerts.
    alerts.clear()
    res2 = await run_monitor(terms=["Aurora"], scrapers=[_fake_scraper], state=state)
    assert res2.fresh == []
    assert alerts == []


@pytest.mark.asyncio
async def test_monitor_tool_registered():
    from app.tools import monitor_tool  # noqa: F401
    from app.tools.registry import registry

    assert "monitor_brand" in registry.names()
