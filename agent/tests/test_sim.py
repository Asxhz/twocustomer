"""Multi-agent simulation — edge cases against the fake "Lumen Flutes" site.

Agents (Monitor→Analyst→Fixer→Validator) communicate over a bus; the site's
output is controllable so we can test detect → fix → validate end to end."""

import pytest

from sim.agents import client_for, detect_product_anomaly, run_swarm
from sim.fake_brand_site import make_site


# ── happy path ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_happy_flute_opportunity():
    bus = await run_swarm(make_site("happy_flute"))
    insights = bus.topic_log("insight")
    assert insights, "should surface an insight from strong positive chatter"
    assert any(i["kind"] == "mention_cluster" for i in insights)
    # no fix needed when it's just praise
    assert bus.topic_log("fix_applied") == []


# ── stockout → restock → validate ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stockout_detected_fixed_validated():
    site = make_site("stockout")
    bus = await run_swarm(site)
    ins = bus.topic_log("insight")
    assert any(i["kind"] == "stockout" and i["severity"] == "risk" for i in ins)
    fixes = bus.topic_log("fix_applied")
    assert any(f["action"] == "restock" for f in fixes)
    vals = bus.topic_log("validation")
    assert any(v["resolved"] for v in vals), "validator should confirm restock resolved it"
    assert site.state.product["in_stock"] is True


# ── PRICE BUG — the centerpiece detect→fix→validate loop ──────────────────────

@pytest.mark.asyncio
async def test_price_bug_full_repair_loop():
    site = make_site("price_bug")
    # site is broken: price is 100x MSRP
    assert detect_product_anomaly(site.state.product)["kind"] == "price_anomaly"

    bus = await run_swarm(site)

    # 1) monitor raised the anomaly
    assert any(s["kind"] == "price_anomaly" for s in bus.topic_log("signal"))
    # 2) analyst turned it into a fixable risk insight
    assert any(i["kind"] == "price_anomaly" and i["fixable"] for i in bus.topic_log("insight"))
    # 3) fixer reset the price
    assert any(f["action"] == "reset_price" for f in bus.topic_log("fix_applied"))
    # 4) validator confirmed resolution
    assert any(v["resolved"] for v in bus.topic_log("validation"))
    # 5) site is actually fixed
    assert site.state.product["price_cents"] == site.state.product["msrp_cents"]
    assert detect_product_anomaly(site.state.product) is None


# ── negative quality spike (insight, not auto-fixable) ────────────────────────

@pytest.mark.asyncio
async def test_negative_quality_insight():
    bus = await run_swarm(make_site("negative"))
    ins = bus.topic_log("insight")
    assert any(i["kind"] == "mention_cluster" for i in ins)
    # product is fine, so no site fix
    assert bus.topic_log("fix_applied") == []


# ── empty feed — graceful, no false signal ────────────────────────────────────

@pytest.mark.asyncio
async def test_empty_feed_no_insight():
    bus = await run_swarm(make_site("empty"))
    assert bus.topic_log("signal") == []
    assert bus.topic_log("insight") == []
    assert bus.topic_log("fix_applied") == []


# ── duplicate posts — dedup catches them ──────────────────────────────────────

@pytest.mark.asyncio
async def test_duplicates_deduped():
    # dupes scenario also has the product out of stock
    bus = await run_swarm(make_site("dupes"))
    mention_signals = [s for s in bus.topic_log("signal") if s["kind"] == "mention"]
    # 3 identical posts (same id) -> exactly one unique mention across all ticks
    assert len(mention_signals) == 1


# ── site error (feed 500) — no crash, no fabricated insight ───────────────────

@pytest.mark.asyncio
async def test_feed_error_degrades_gracefully():
    bus = await run_swarm(make_site("error"))  # /feed 500s
    assert [s for s in bus.topic_log("signal") if s["kind"] == "mention"] == []
    # product is healthy in this scenario, so no anomaly either
    assert bus.topic_log("fix_applied") == []


# ── site SWITCHES output mid-run — agents react to the change ─────────────────

@pytest.mark.asyncio
async def test_site_switches_output_midrun():
    from sim.agents import (AnalystAgent, Bus, FixerAgent, MonitorAgent,
                            ValidatorAgent)

    site = make_site("happy_flute")
    bus = Bus()
    async with client_for(site) as c:
        mon, ana, fix, val = (MonitorAgent(c, bus), AnalystAgent(bus),
                              FixerAgent(c, bus), ValidatorAgent(c, bus))
        # tick 1: healthy site
        await mon.tick(); await ana.tick(); await fix.tick(); await val.tick()
        assert not any(s["kind"] == "price_anomaly" for s in bus.topic_log("signal"))

        # the site changes its output (a deploy introduces the price bug)
        await c.post("/admin/scenario", json={"scenario": "price_bug"})

        # tick 2: agents detect + repair the new problem
        await mon.tick(); await ana.tick(); await fix.tick(); await val.tick()
    assert any(s["kind"] == "price_anomaly" for s in bus.topic_log("signal"))
    assert any(f["action"] == "reset_price" for f in bus.topic_log("fix_applied"))
    assert site.state.product["price_cents"] == site.state.product["msrp_cents"]


# ── a fix is durable — re-running finds nothing new to fix ────────────────────

@pytest.mark.asyncio
async def test_fix_is_durable():
    site = make_site("price_bug")
    await run_swarm(site)                       # fixes it
    bus2 = await run_swarm(site)                # run again on the fixed site
    assert detect_product_anomaly(site.state.product) is None
    assert bus2.topic_log("fix_applied") == []  # nothing left to fix
