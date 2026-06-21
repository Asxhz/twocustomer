"""TwoCustomer Discord gateway bot (standalone, runs on this machine).

A persistent websocket bot (not HTTP-interactions) so slash commands work without
configuring an interactions endpoint. It is a thin Discord I/O layer: each command
forwards to the TwoCustomer agent (local or deployed) which holds the brains
(linking, fixes, DMs). Run:

    DISCORD_BOT_TOKEN=... DISCORD_GUILD_ID=... AGENT_BASE_URL=... AGENT_SHARED_TOKEN=... \
    agent/.venv/bin/python agent/bot.py

AGENT_BASE_URL can point at the deployed Vercel agent (real project) or localhost.
"""

from __future__ import annotations

import asyncio
import os

import discord
import httpx
from discord import app_commands

from app.config import get_settings

S = get_settings()
# Use the local agent by default (shares this machine's AGENT_SHARED_TOKEN and the
# local voice control, so the agent can join calls). Override with AGENT_BASE_URL.
AGENT = (os.environ.get("AGENT_BASE_URL") or S.agent_base_url or "http://localhost:8000").rstrip("/")
GUILD_ID = os.environ.get("DISCORD_GUILD_ID") or S.discord_guild_id


def _headers() -> dict[str, str]:
    tok = S.shared_token
    return {"Authorization": f"Bearer {tok}"} if tok else {}


async def _post(path: str, body: dict) -> str:
    last = ""
    for attempt in range(3):  # retry transient connection failures
        try:
            async with httpx.AsyncClient(timeout=300) as c:
                r = await c.post(f"{AGENT}{path}", json=body,
                                 headers={**_headers(), "Content-Type": "application/json"})
                if r.status_code != 200:
                    return f"Agent error ({r.status_code}). Try again in a moment."
                return r.json().get("reply", "Done.")
        except Exception as exc:  # noqa: BLE001
            last = str(exc)
            await asyncio.sleep(1.5 * (attempt + 1))
    return f"Couldn't reach the agent right now ({last}). Please try again."


intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@tree.command(name="setup", description="Link this server to your TwoCustomer account (admin only).")
@app_commands.describe(email="The email you signed up with")
async def setup_cmd(interaction: discord.Interaction, email: str):
    await interaction.response.defer(thinking=True, ephemeral=True)
    is_admin = bool(interaction.user.guild_permissions.administrator) if interaction.guild else False
    reply = await _post("/discord/setup", {
        "guild_id": str(interaction.guild_id or ""), "is_admin": is_admin, "email": email,
    })
    await interaction.followup.send(reply, ephemeral=True)


async def _report(interaction: discord.Interaction, text: str | None):
    await interaction.response.defer(thinking=True, ephemeral=True)
    reply = await _post("/discord/report", {
        "guild_id": str(interaction.guild_id or ""),
        "user_id": str(interaction.user.id), "text": text or "",
    })
    await interaction.followup.send(reply, ephemeral=True)


@tree.command(name="report", description="Report a problem. I'll get on a call and fix it.")
@app_commands.describe(text="What's broken")
async def report_cmd(interaction: discord.Interaction, text: str | None = None):
    await _report(interaction, text)


@tree.command(name="rec", description="Share a recommendation or idea. I'll prototype it.")
@app_commands.describe(text="Your recommendation")
async def rec_cmd(interaction: discord.Interaction, text: str | None = None):
    await _report(interaction, text)


@tree.command(name="idea", description="Share an idea or change. I'll prototype it with you.")
@app_commands.describe(text="Your idea")
async def idea_cmd(interaction: discord.Interaction, text: str | None = None):
    await _report(interaction, text)


@client.event
async def on_ready():
    try:
        if GUILD_ID:
            g = discord.Object(id=int(GUILD_ID))
            tree.copy_global_to(guild=g)
            await tree.sync(guild=g)
            print(f"Bot ready as {client.user}. Commands synced to guild {GUILD_ID}.")
        else:
            await tree.sync()
            print(f"Bot ready as {client.user}. Global commands synced (may take ~1h).")
        print(f"Agent: {AGENT}")
    except Exception as exc:  # noqa: BLE001
        print(f"Command sync failed: {exc}")


def main() -> int:
    token = S.discord_bot_token
    if not token:
        print("DISCORD_BOT_TOKEN not set.")
        return 1
    client.run(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
