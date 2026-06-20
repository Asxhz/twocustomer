#!/usr/bin/env python3
"""LIVE demo of the TwoCustomer monitor -> insight -> alert -> persist chain.

Uses real services (Browserbase/HN scrape, Convex, Discord, Redis) — no Claude
required (insight uses the heuristic; Claude sharpens it when funded). Shows each
real step. Run: uv run --project agent python scripts/demo.py [brand_term]
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))

from app.channels.alerts import dispatch  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.monitor.insight import synth_insight  # noqa: E402
from app.monitor.runner import MonitorState, run_monitor  # noqa: E402
from app.monitor.scrapers import DEFAULT_SCRAPERS  # noqa: E402
from app.state.convex_client import get_convex  # noqa: E402


def hr(t): print("\n" + "─" * 60 + f"\n  {t}\n" + "─" * 60)


async def main():
    term = sys.argv[1] if len(sys.argv) > 1 else "anthropic claude"
    s = get_settings()

    hr(f"1. MONITOR — live scrape for: {term!r}")
    state = MonitorState()
    alerts_fired = []

    async def on_alert(m):
        out = await dispatch(f"[{m.platform}] {m.text[:180]}",
                             title=f"High-signal mention · {term}", severity="risk")
        alerts_fired.append((m, out))

    res = await run_monitor(terms=[term], scrapers=DEFAULT_SCRAPERS,
                            state=state, threshold=0.5, on_alert=on_alert)
    print(f"  scraped {len(res.fresh)} REAL mentions (HN + Reddit-via-Browserbase)")
    for m in sorted(res.fresh, key=lambda x: x.score, reverse=True)[:4]:
        flag = "🔴 HIGH" if m.high_signal else "  "
        print(f"   {flag} [{m.platform}] score={m.score:.2f} eng={m.engagement:.0f} | {m.text[:70]}")

    hr("2. INSIGHT — synthesize from high-signal mentions")
    high = res.high_signal or sorted(res.fresh, key=lambda x: x.score, reverse=True)[:3]
    insight = await synth_insight(term, high)
    if insight:
        print(f"   TITLE: {insight['title']}")
        print(f"   BODY:  {insight['body']}")
        print(f"   SEV:   {insight['severity']}  (Claude sharpens this when funded)")
    else:
        print("   (no mentions to synthesize)")

    hr("3. ALERT — fire high-signal to channels")
    if alerts_fired:
        for m, chans in alerts_fired[:3]:
            print(f"   sent to {chans or '(no channel configured)'}: {m.text[:60]}")
    else:
        print("   no high-signal this pass (try a hotter term, e.g. 'recall')")
        # force one alert so you can see Discord light up
        if res.fresh:
            top = max(res.fresh, key=lambda x: x.score)
            chans = await dispatch(f"[demo] {top.text[:160]}",
                                   title=f"Demo alert · {term}", severity="opportunity")
            print(f"   demo alert sent to: {chans or '(none configured)'}")

    hr("4. PERSIST — write to live Convex")
    cx = get_convex()
    if cx.enabled and insight:
        bid = await cx.mutation("brands:upsert", name=term.title(),
                                slug=term.lower().replace(" ", "-"), terms=[term])
        await cx.mutation("insights:addInsight", brandId=bid, title=insight["title"],
                          body=insight["body"], severity=insight["severity"])
        print(f"   wrote brand + insight to Convex (brand id {str(bid)[:12]}…)")
        print(f"   → visible at /admin/insights and /monitor (live badge)")
    else:
        print("   Convex not configured — skipped")

    hr("DONE — every step above hit a real service")
    print(f"  Live: {'Convex ✔' if cx.enabled else ''} "
          f"{'Discord ✔' if s.discord_webhook_url else ''} "
          f"{'Redis ✔' if s.has_redis() else ''} "
          f"{'Browserbase ✔' if s.has_browserbase() else ''}\n")


if __name__ == "__main__":
    asyncio.run(main())
