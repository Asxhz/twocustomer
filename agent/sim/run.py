"""Narrated run of the agent swarm — watch the agents communicate and repair a
broken site. Run: uv run --project agent python -m sim.run [scenario]"""

from __future__ import annotations

import asyncio
import sys

from .agents import detect_product_anomaly, run_swarm
from .fake_brand_site import make_site

LABEL = {"signal": "🛰  Monitor", "insight": "🧠 Analyst",
         "fix_applied": "🔧 Fixer", "validation": "✅ Validator"}


def line(topic, msg):
    who = LABEL.get(topic, topic)
    if topic == "signal":
        if msg["kind"] == "mention":
            tag = "🔴" if msg.get("high_signal") else "  "
            return f"{who:<12} | signal {tag} [{msg['platform']}] {msg['text'][:60]} (score {msg['score']})"
        return f"{who:<12} | signal ⚠ {msg['kind'].upper()} {msg.get('ratio','')}"
    if topic == "insight":
        return f"{who:<12} | INSIGHT [{msg['severity']}] {msg['title']}"
    if topic == "fix_applied":
        b, a = msg["before"], msg["after"]
        return f"{who:<12} | applied '{msg['action']}'  price ${b['price_cents']/100:.0f}→${a['price_cents']/100:.0f}  stock {b['in_stock']}→{a['in_stock']}"
    if topic == "validation":
        return f"{who:<12} | resolved={msg['resolved']}  → site healthy" if msg["resolved"] else f"{who:<12} | NOT resolved"
    return f"{who} | {msg}"


async def main():
    scenario = sys.argv[1] if len(sys.argv) > 1 else "price_bug"
    site = make_site(scenario)
    p = site.state.product
    print("=" * 70)
    print(f"  LUMEN FLUTES — scenario: {scenario}")
    print(f"  site state: price ${p['price_cents']/100:.0f} (MSRP ${p['msrp_cents']/100:.0f}), "
          f"in_stock={p['in_stock']}")
    anom = detect_product_anomaly(p)
    print(f"  problem present: {anom['kind'] if anom else 'none'}")
    print("=" * 70 + "\n  --- agents communicating ---\n")

    bus = await run_swarm(site, ticks=2)
    for topic, msg in bus.log:
        print("  " + line(topic, msg))

    p = site.state.product
    print("\n" + "=" * 70)
    print(f"  FINAL site state: price ${p['price_cents']/100:.0f}, in_stock={p['in_stock']}, "
          f"fixes applied={site.state.fixes}")
    print(f"  problem present now: {(detect_product_anomaly(p) or {}).get('kind', 'none')}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
