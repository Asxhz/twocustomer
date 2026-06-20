"""Slack channel — signature verification, event routing, alerts.

Brand-side channel: high-signal monitor alerts are pushed in; `/twocustomer`
slash commands and @mentions route to the Claude agent loop.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any

import httpx

from app.config import get_settings

_API = "https://slack.com/api"


def verify_signature(
    *, signing_secret: str, timestamp: str, body: str, signature: str,
    max_skew: int = 300, now: float | None = None,
) -> bool:
    """Verify a Slack request signature (v0 HMAC-SHA256).

    Pure function — testable offline. Rejects stale timestamps (replay guard).
    """
    if not signing_secret or not signature:
        return False
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        return False
    current = now if now is not None else time.time()
    if abs(current - ts) > max_skew:
        return False
    basestring = f"v0:{timestamp}:{body}".encode()
    digest = hmac.new(signing_secret.encode(), basestring, hashlib.sha256).hexdigest()
    expected = f"v0={digest}"
    return hmac.compare_digest(expected, signature)


def is_configured() -> bool:
    return bool(get_settings().slack_bot_token)


async def post_message(channel: str, text: str,
                       blocks: list[dict[str, Any]] | None = None) -> bool:
    """Post a message to a Slack channel via the Web API."""
    s = get_settings()
    if not s.slack_bot_token:
        return False
    payload: dict[str, Any] = {"channel": channel, "text": text}
    if blocks:
        payload["blocks"] = blocks
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(
            f"{_API}/chat.postMessage",
            headers={"Authorization": f"Bearer {s.slack_bot_token}",
                     "Content-Type": "application/json; charset=utf-8"},
            json=payload,
        )
        return bool(r.json().get("ok"))


def insight_blocks(title: str, body: str, severity: str = "info") -> list[dict[str, Any]]:
    """Block-kit card for a high-signal insight alert."""
    icon = {"risk": "🔴", "opportunity": "🟢"}.get(severity, "🔵")
    return [
        {"type": "header",
         "text": {"type": "plain_text", "text": f"{icon} {title}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": body}},
        {"type": "context",
         "elements": [{"type": "mrkdwn", "text": "TwoCustomer · live monitor"}]},
    ]


async def alert(text: str, *, title: str = "High-signal mention",
                severity: str = "info") -> bool:
    """Push a high-signal alert to the configured alert channel."""
    s = get_settings()
    if not s.slack_alert_channel:
        return False
    return await post_message(
        s.slack_alert_channel, text,
        blocks=insight_blocks(title, text, severity),
    )
