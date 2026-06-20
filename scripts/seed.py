#!/usr/bin/env python3
"""Seed a demo consumer brand + a few mentions into Convex.

Idempotent-ish: inserts a brand and sample mentions. Requires CONVEX_URL; if
unset, prints the payload it *would* send so the script is still runnable.
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))

from app.state.convex_client import get_convex  # noqa: E402

DEMO_BRAND = {
    "name": "Aurora Drinks",
    "slug": "aurora-drinks",
    "terms": ["Aurora Drinks", "@auroradrinks", "aurora sparkling"],
    "handles": {"x": "auroradrinks", "reddit": "auroradrinks"},
}

DEMO_MENTIONS = [
    {"platform": "x", "externalId": "x1", "author": "@thirsty_sam",
     "text": "Aurora Drinks sold out at my Whole Foods AGAIN. third week in a row.",
     "url": "https://x.com/thirsty_sam/status/1", "score": 0.92, "highSignal": True},
    {"platform": "reddit", "externalId": "r1", "author": "u/cpg_nerd",
     "text": "Anyone else notice Aurora's new can design? sales seem up.",
     "url": "https://reddit.com/r/cpg/1", "score": 0.55, "highSignal": False},
    {"platform": "web", "externalId": "w1", "author": "BevReview",
     "text": "Aurora Drinks review: the yuzu flavor is the breakout SKU this quarter.",
     "url": "https://bevreview.com/aurora", "score": 0.7, "highSignal": True},
]


async def main() -> int:
    cx = get_convex()
    if not cx.enabled:
        print("CONVEX_URL not set — dry run. Would seed:")
        print(" brand:", DEMO_BRAND)
        for m in DEMO_MENTIONS:
            print(" mention:", m["externalId"], m["text"][:50])
        return 0

    brand_id = await cx.mutation("brands:upsert", **DEMO_BRAND)
    print("brand:", brand_id)
    now = int(time.time() * 1000)
    for m in DEMO_MENTIONS:
        res = await cx.mutation("mentions:insertMention", brandId=brand_id,
                                ts=now, **m)
        print("mention", m["externalId"], "->", res)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
