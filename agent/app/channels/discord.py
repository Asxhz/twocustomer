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


async def followup(interaction_token: str, content: str) -> None:
    """Send the real reply after a deferred ack (3s rule)."""
    s = get_settings()
    if not s.discord_app_id:
        return
    async with httpx.AsyncClient(timeout=20) as c:
        await c.post(
            f"{_API}/webhooks/{s.discord_app_id}/{interaction_token}",
            json={"content": content[:1900]},
        )


# ── Outbound: alerts via incoming webhook ─────────────────────────────────────

async def alert(text: str, *, title: str = "High-signal mention",
                severity: str = "info") -> bool:
    s = get_settings()
    if not s.discord_webhook_url:
        return False
    color = {"risk": 0xE74C3C, "opportunity": 0x2ECC71}.get(severity, 0x3498DB)
    embed = {"title": title, "description": text[:1900], "color": color,
             "footer": {"text": "TwoCustomer · live monitor"}}
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(s.discord_webhook_url, json={"embeds": [embed]})
        return r.status_code in (200, 204)
