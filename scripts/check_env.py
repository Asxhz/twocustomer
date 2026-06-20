#!/usr/bin/env python3
"""Report which TwoCustomer env keys are set. Reads .env / .env.local / process env.

Usage: python scripts/check_env.py
Exit 0 always; prints a table grouped by phase/sponsor.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(p: Path) -> None:
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


_load(ROOT / ".env")
_load(ROOT / ".env.local")

GROUPS: dict[str, list[str]] = {
    "Anthropic (P2)": ["ANTHROPIC_API_KEY", "ANTHROPIC_MODEL"],
    "Browserbase (P3)": ["BROWSERBASE_API_KEY", "BROWSERBASE_PROJECT_ID"],
    "Deepgram (P4)": ["DEEPGRAM_API_KEY"],
    "Gemini (Edit)": ["GEMINI_API_KEY"],
    "Daily (video)": ["DAILY_API_KEY", "DAILY_DOMAIN"],
    "Twilio (SMS/call)": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER"],
    "Vercel (FDE preview)": ["VERCEL_TOKEN"],
    "Discord": ["DISCORD_PUBLIC_KEY", "DISCORD_WEBHOOK_URL"],
    "Slack (P4)": ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET", "SLACK_ALERT_CHANNEL"],
    "Fetch/ASI:One (P5)": ["ASI_ONE_API_KEY", "AGENTVERSE_API_KEY", "UAGENT_SEED"],
    "Upstash Redis (P6)": ["UPSTASH_REDIS_REST_URL", "UPSTASH_REDIS_REST_TOKEN"],
    "Convex (P1)": ["CONVEX_URL"],
    "Stretch": ["SENTRY_DSN", "ARIZE_API_KEY"],
}


def main() -> int:
    print("TwoCustomer env check\n" + "=" * 40)
    total = set_count = 0
    for group, keys in GROUPS.items():
        print(f"\n{group}")
        for k in keys:
            val = os.environ.get(k, "")
            total += 1
            ok = bool(val)
            set_count += ok
            mark = "✓" if ok else "·"
            shown = "set" if ok else "MISSING"
            print(f"  {mark} {k:<28} {shown}")
    print("\n" + "=" * 40)
    print(f"{set_count}/{total} keys set")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
