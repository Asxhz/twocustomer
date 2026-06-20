#!/usr/bin/env python3
"""End-to-end smoke for the TwoCustomer control plane.

Exercises the full local path that does NOT require external keys:
  health → tool registry → monitor run (injected scraper) → memory recall.
Live integrations (Claude reply, Browserbase, Deepgram, Slack, ASI:One) are
reported as configured/unconfigured but not called, so this passes offline.

Run: python scripts/e2e_smoke.py
Exit 0 on success.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))

from app.config import get_settings  # noqa: E402
from app.monitor.mention import normalize  # noqa: E402
from app.monitor.runner import MonitorState, run_monitor  # noqa: E402
from app.state import memory  # noqa: E402
from app.tools import echo, memory_tool, monitor_tool  # noqa: E402,F401
from app.tools.registry import registry  # noqa: E402


async def _fake_scraper(term: str):
    return [
        normalize("reddit", external_id="s1",
                  text=f"{term} sold out again", engagement=2),
        normalize("reddit", external_id="s2",
                  text=f"{term} yuzu is amazing", engagement=800),
    ]


async def main() -> int:
    s = get_settings()
    ok = True

    print("== config ==")
    for name, val in [
        ("anthropic", s.has_anthropic()), ("convex", s.has_convex()),
        ("redis", s.has_redis()), ("browserbase", s.has_browserbase()),
    ]:
        print(f"  {'✓' if val else '·'} {name}")

    print("== tools ==")
    tools = registry.names()
    for need in ("echo", "recall_memory", "monitor_brand"):
        present = need in tools
        ok &= present
        print(f"  {'✓' if present else '✗'} {need}")

    print("== monitor run ==")
    res = await run_monitor(terms=["Aurora Drinks"], scrapers=[_fake_scraper],
                            state=MonitorState())
    ok &= len(res.fresh) == 2 and len(res.high_signal) >= 1
    print(f"  fresh={len(res.fresh)} high_signal={len(res.high_signal)}")

    print("== memory recall ==")
    await memory.remember("aurora", item_id="m1", kind="insight",
                          text="stockouts cost 10% of revenue")
    hits = await memory.recall("aurora", "why losing revenue stockouts", k=1)
    ok &= bool(hits)
    print(f"  recalled={len(hits)}")

    print("\n" + ("E2E SMOKE PASS ✅" if ok else "E2E SMOKE FAIL ❌"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
