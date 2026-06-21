#!/usr/bin/env python3
"""Register TwoCustomer's Discord slash commands.

Needs DISCORD_BOT_TOKEN + DISCORD_APP_ID. If DISCORD_GUILD_ID is set, registers
guild commands (instant); otherwise global (can take up to ~1h to appear).

Run: agent/.venv/bin/python scripts/register_discord.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))

import httpx  # noqa: E402

from app.config import get_settings  # noqa: E402

API = "https://discord.com/api/v10"
USER_OPTION = 6  # Discord application command option type for a user

COMMANDS = [
    {
        "name": "twocustomer",
        "description": "Ask TwoCustomer to monitor, research, fix, or build.",
        "options": [{"name": "text", "description": "What to do", "type": 3, "required": True}],
    },
    {
        "name": "invite",
        "description": "Invite someone to sign up (DMs them a link).",
        "options": [
            {"name": "user", "description": "Who to invite", "type": USER_OPTION, "required": True},
            {"name": "brand", "description": "Brand slug (optional)", "type": 3, "required": False},
        ],
    },
    {
        "name": "join",
        "description": "Send someone a live call link.",
        "options": [{"name": "user", "description": "Who to call", "type": USER_OPTION, "required": False}],
    },
    {
        "name": "setup",
        "description": "Link this server to your TwoCustomer account (admin only).",
        "options": [{"name": "email", "description": "The email you signed up with",
                     "type": 3, "required": True}],
    },
    {
        "name": "report",
        "description": "Report a problem. I'll get on a call and fix it.",
        "options": [{"name": "text", "description": "What's broken", "type": 3, "required": False}],
    },
    {
        "name": "idea",
        "description": "Share an idea or change. I'll prototype it with you.",
        "options": [{"name": "text", "description": "Your idea", "type": 3, "required": False}],
    },
]


async def main() -> int:
    s = get_settings()
    if not (s.discord_bot_token and s.discord_app_id):
        print("Set DISCORD_BOT_TOKEN and DISCORD_APP_ID first.")
        return 1
    guild = s.discord_guild_id
    url = (f"{API}/applications/{s.discord_app_id}/guilds/{guild}/commands"
           if guild else f"{API}/applications/{s.discord_app_id}/commands")
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.put(url, headers={"Authorization": f"Bot {s.discord_bot_token}"}, json=COMMANDS)
    if r.status_code in (200, 201):
        print(f"Registered {len(COMMANDS)} commands ({'guild' if guild else 'global'}).")
        return 0
    print(f"Failed: {r.status_code} {r.text[:300]}")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
