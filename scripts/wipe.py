#!/usr/bin/env python3
"""Wipe ALL data from the live Convex deployment so the app starts empty + real.

Destructive + irreversible. Real signup + connections + monitoring repopulate it.
Run: agent/.venv/bin/python scripts/wipe.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))

from app.state.convex_client import get_convex  # noqa: E402


async def main() -> int:
    cx = get_convex()
    if not cx.enabled:
        print("CONVEX_URL not set; nothing to wipe.")
        return 0
    n = await cx.mutation("admin:wipeAll")
    print(f"Wiped {n} rows. Convex is now empty.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
