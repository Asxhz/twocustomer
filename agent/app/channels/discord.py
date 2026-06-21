"""Discord channel — free alternative to Slack.

- Inbound: slash commands via Discord's HTTP Interactions (Ed25519-verified),
  routed to the Claude agent loop. `/twocustomer <text>`.
- Outbound: high-signal alerts posted to a channel via an incoming webhook.

Discord is also the natural customer-signal intake surface for a brand (bug
reports / feedback land in their server), feeding the same monitor → insight loop.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings

_API = "https://discord.com/api/v10"


# ── Inbound: interaction signature verification (Ed25519) ─────────────────────

def verify_signature(*, public_key: str, signature: str, timestamp: str,
                     body: str) -> bool:
    """Verify a Discord interaction request signature. Pure → testable offline."""
    if not public_key or not signature or not timestamp:
        return False
    try:
        from nacl.exceptions import BadSignatureError
        from nacl.signing import VerifyKey

        vk = VerifyKey(bytes.fromhex(public_key))
        vk.verify(f"{timestamp}{body}".encode(), bytes.fromhex(signature))
        return True
    except (BadSignatureError, ValueError, Exception):  # noqa: BLE001
        return False


def is_configured() -> bool:
    return bool(get_settings().discord_public_key)


# Interaction + response type enums (Discord)
PING = 1
APPLICATION_COMMAND = 2
PONG = 1
CHANNEL_MESSAGE = 4
DEFERRED_MESSAGE = 5


def command_text(payload: dict[str, Any]) -> str:
    """Extract the user's text from a slash-command interaction."""
    data = payload.get("data", {})
    opts = data.get("options", [])
    for o in opts:
        if o.get("name") in ("text", "query", "message", "prompt"):
            return str(o.get("value", ""))
    # fall back to the first string option, else the command name
    for o in opts:
        if isinstance(o.get("value"), str):
            return str(o["value"])
    return data.get("name", "")


def command_name(payload: dict[str, Any]) -> str:
    return str(payload.get("data", {}).get("name", ""))


def command_option(payload: dict[str, Any], name: str) -> str:
    for o in payload.get("data", {}).get("options", []):
        if o.get("name") == name:
            return str(o.get("value", ""))
    return ""


def invoking_user_id(payload: dict[str, Any]) -> str:
    # In a guild: payload.member.user.id; in DM: payload.user.id
    member = payload.get("member") or {}
    user = member.get("user") or payload.get("user") or {}
    return str(user.get("id", ""))


async def dm(user_id: str, content: str) -> bool:
    """Open a DM channel with a user and send a message. Needs DISCORD_BOT_TOKEN."""
    s = get_settings()
    if not (s.discord_bot_token and user_id):
        return False
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            ch = await c.post(
                f"{_API}/users/@me/channels",
                headers={"Authorization": f"Bot {s.discord_bot_token}"},
                json={"recipient_id": user_id})
            if ch.status_code not in (200, 201):
                return False
            cid = ch.json().get("id")
            r = await c.post(
                f"{_API}/channels/{cid}/messages",
                headers={"Authorization": f"Bot {s.discord_bot_token}"},
                json={"content": content[:1900]})
            return r.status_code in (200, 201)
    except Exception:  # noqa: BLE001
        return False


async def followup(interaction_token: str, content: str) -> None:
    """Send the real reply after a deferred ack (3s rule)."""
    s = get_settings()
    if not s.discord_app_id:
        return
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            await c.post(
                f"{_API}/webhooks/{s.discord_app_id}/{interaction_token}",
                json={"content": content[:1900]},
            )
    except Exception:  # noqa: BLE001
        pass


# ── Inbound: read team context from a channel ─────────────────────────────────

async def list_guilds() -> list[dict[str, Any]]:
    """Guilds the bot is in (needs DISCORD_BOT_TOKEN)."""
    s = get_settings()
    if not s.discord_bot_token:
        return []
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"{_API}/users/@me/guilds",
                            headers={"Authorization": f"Bot {s.discord_bot_token}"})
            return r.json() if r.status_code == 200 else []
    except Exception:  # noqa: BLE001
        return []


async def read_context(channel_id: str | None = None, *, limit: int = 20) -> str:
    """Return recent messages from a channel as plain text the agent can use as
    context. Defaults to DISCORD_CHANNEL_ID. Empty string when unavailable."""
    s = get_settings()
    cid = channel_id or s.discord_channel_id
    if not (s.discord_bot_token and cid):
        return ""
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(
                f"{_API}/channels/{cid}/messages",
                headers={"Authorization": f"Bot {s.discord_bot_token}"},
                params={"limit": min(limit, 50)})
        if r.status_code != 200:
            return ""
        msgs = r.json()
    except Exception:  # noqa: BLE001
        return ""
    lines = []
    for m in reversed(msgs):  # oldest first
        author = m.get("author", {}).get("username", "?")
        text = (m.get("content") or "").strip()
        if text:
            lines.append(f"{author}: {text}")
    return "\n".join(lines)


# ── Outbound: alerts via incoming webhook ─────────────────────────────────────

async def alert(text: str, *, title: str = "High-signal mention",
                severity: str = "info") -> bool:
    s = get_settings()
    if not s.discord_webhook_url:
        return False
    color = {"risk": 0xE74C3C, "opportunity": 0x2ECC71}.get(severity, 0x3498DB)
    embed = {"title": title, "description": text[:1900], "color": color,
             "footer": {"text": "TwoCustomer · live monitor"}}
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(s.discord_webhook_url, json={"embeds": [embed]})
            return r.status_code in (200, 204)
    except Exception:  # noqa: BLE001
        return False
