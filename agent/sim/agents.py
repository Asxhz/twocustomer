"""Multi-agent swarm for the sim. Four agents communicate over an async Bus:

  MonitorAgent  → scrapes the fake site, scores signal, publishes "signal"
  AnalystAgent  → consumes signals, synthesizes "insight"
  FixerAgent    → consumes fixable insights, calls the site's /admin/fix, publishes "fix_applied"
  ValidatorAgent→ consumes fixes, re-scrapes, confirms resolution, publishes "validation"

They use the REAL monitor code (normalize / Baseline scoring / dedup / heuristic
insight). The site is reached over real HTTP via httpx's ASGI transport.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import httpx
from httpx import ASGITransport

from app.monitor.dedup import dedup, seen_key
from app.monitor.insight import _heuristic
from app.monitor.mention import normalize
from app.monitor.scoring import Baseline, score_batch


def client_for(app) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://lumen.test")


# ── message bus ───────────────────────────────────────────────────────────────

@dataclass
class Bus:
    queues: dict[str, asyncio.Queue] = field(default_factory=lambda: defaultdict(asyncio.Queue))
    log: list[tuple[str, dict]] = field(default_factory=list)

    async def pub(self, topic: str, msg: dict) -> None:
        self.log.append((topic, msg))
        await self.queues[topic].put(msg)

    def drain(self, topic: str) -> list[dict]:
        out, q = [], self.queues[topic]
        while not q.empty():
            out.append(q.get_nowait())
        return out

    def topic_log(self, topic: str) -> list[dict]:
        return [m for t, m in self.log if t == topic]


# ── anomaly detection (product page) ──────────────────────────────────────────

def detect_product_anomaly(product: dict[str, Any]) -> dict[str, Any] | None:
    if not product.get("in_stock", True):
        return {"kind": "stockout", "fix_action": "restock"}
    price, msrp = product.get("price_cents", 0), product.get("msrp_cents", 0)
    if msrp and price / msrp >= 3:
        return {"kind": "price_anomaly", "fix_action": "reset_price",
                "ratio": round(price / msrp, 1), "price_cents": price, "msrp_cents": msrp}
    return None


# ── agents ────────────────────────────────────────────────────────────────────

class MonitorAgent:
    def __init__(self, client, bus, brand="lumen-flutes"):
        self.c, self.bus, self.brand = client, bus, brand
        self.seen: set[str] = set()
        self.baseline = Baseline()

    async def tick(self) -> None:
        # 1) social feed → mentions
        try:
            r = await self.c.get("/feed")
            mentions_raw = r.json().get("mentions", []) if r.status_code == 200 else []
        except Exception:
            mentions_raw = []
        ms = [normalize("web", external_id=m["id"], text=m["text"],
                        author=m["author"], engagement=float(m.get("likes", 0)))
              for m in mentions_raw]
        fresh = dedup(ms, self.seen)
        scored = score_batch(fresh, self.baseline, threshold=0.6)
        for m in scored:
            await self.bus.pub("signal", {"kind": "mention", "platform": m.platform,
                                          "text": m.text, "author": m.author,
                                          "score": m.score, "high_signal": m.high_signal})
        # 2) product page → anomaly
        try:
            p = (await self.c.get("/product")).json()
        except Exception:
            p = {}
        anom = detect_product_anomaly(p)
        if anom:
            await self.bus.pub("signal", anom)


class AnalystAgent:
    def __init__(self, bus):
        self.bus = bus

    async def tick(self) -> None:
        signals = self.bus.drain("signal")
        if not signals:
            return
        anomalies = [s for s in signals if s["kind"] in ("price_anomaly", "stockout")]
        high = [s for s in signals if s["kind"] == "mention" and s.get("high_signal")]

        for a in anomalies:
            if a["kind"] == "price_anomaly":
                title = f"Pricing bug: flute listed at {a['ratio']}x MSRP"
                body = (f"Product page shows ${a['price_cents']/100:.0f} vs "
                        f"${a['msrp_cents']/100:.0f} MSRP. Customers noticing — revenue + trust risk.")
            else:
                title = "Stockout: flute unavailable during demand spike"
                body = "Product is out of stock while customers are actively trying to buy."
            await self.bus.pub("insight", {"kind": a["kind"], "title": title, "body": body,
                                           "severity": "risk", "fixable": True,
                                           "fix_action": a["fix_action"]})
        if high:
            # reuse the real heuristic to phrase the mention-cluster insight
            class _M:  # minimal shim for _heuristic (needs .score/.text/.author/.platform)
                def __init__(s, d): s.__dict__.update(d)
            shims = [_M({"score": s["score"], "text": s["text"],
                         "author": s["author"], "platform": s["platform"]}) for s in high]
            h = _heuristic("lumen-flutes", shims)
            await self.bus.pub("insight", {**h, "kind": "mention_cluster", "fixable": False})


class FixerAgent:
    def __init__(self, client, bus):
        self.c, self.bus = client, bus

    async def tick(self) -> None:
        for ins in self.bus.drain("insight"):
            if not ins.get("fixable"):
                continue
            before = (await self.c.get("/product")).json()
            await self.c.post("/admin/fix", json={"action": ins["fix_action"]})
            after = (await self.c.get("/product")).json()
            await self.bus.pub("fix_applied", {"action": ins["fix_action"],
                                               "insight_title": ins["title"],
                                               "before": before, "after": after})


class ValidatorAgent:
    def __init__(self, client, bus):
        self.c, self.bus = client, bus

    async def tick(self) -> None:
        for fix in self.bus.drain("fix_applied"):
            product = (await self.c.get("/product")).json()
            resolved = detect_product_anomaly(product) is None
            await self.bus.pub("validation", {"action": fix["action"],
                                              "resolved": resolved,
                                              "product": product})


async def run_swarm(app, *, ticks: int = 3) -> Bus:
    """Run Monitor→Analyst→Fixer→Validator for N sequential ticks. Returns the bus."""
    bus = Bus()
    async with client_for(app) as c:
        mon, ana = MonitorAgent(c, bus), AnalystAgent(bus)
        fix, val = FixerAgent(c, bus), ValidatorAgent(c, bus)
        for _ in range(ticks):
            await mon.tick()
            await ana.tick()
            await fix.tick()
            await val.tick()
    return bus
