"""Twilio channel — SMS + phone-call customer interviews.

- SMS: webhook in (signature-verified) → interview FSM → reply <Message>.
- Voice: agent can place an outbound call; the call runs the interview via
  TwiML <Gather input="speech"> (Twilio's speech recognition) — robust without a
  media stream. Deepgram remains available for browser voice.

Signature verification (X-Twilio-Signature): HMAC-SHA1 of the full URL +
sorted POST params, keyed by the auth token, base64-encoded.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Any
from xml.sax.saxutils import escape

import httpx

from app.config import get_settings

_API = "https://api.twilio.com/2010-04-01"


def is_configured() -> bool:
    s = get_settings()
    return bool(s.twilio_account_sid and s.twilio_auth_token)


def verify_signature(*, auth_token: str, signature: str, url: str,
                     params: dict[str, str]) -> bool:
    """Verify a Twilio request signature. Pure → testable offline."""
    if not auth_token or not signature:
        return False
    base = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    digest = hmac.new(auth_token.encode(), base.encode(), hashlib.sha1).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, signature)


# ── TwiML builders ────────────────────────────────────────────────────────────

def twiml_message(text: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{escape(text)}</Message></Response>'


def twiml_say_gather(say: str, *, action: str, end: bool = False) -> str:
    body = f"<Say>{escape(say)}</Say>"
    if not end:
        body += (f'<Gather input="speech" speechTimeout="auto" method="POST" '
                 f'action="{escape(action)}"><Say>Go ahead.</Say></Gather>')
    else:
        body += "<Hangup/>"
    return f'<?xml version="1.0" encoding="UTF-8"?><Response>{body}</Response>'


# ── Outbound ──────────────────────────────────────────────────────────────────

async def send_sms(to: str, body: str) -> bool:
    s = get_settings()
    if not is_configured() or not s.twilio_from_number:
        return False
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(
            f"{_API}/Accounts/{s.twilio_account_sid}/Messages.json",
            auth=(s.twilio_account_sid, s.twilio_auth_token),
            data={"To": to, "From": s.twilio_from_number, "Body": body[:1500]},
        )
        return r.status_code in (200, 201)


async def place_call(to: str, *, voice_url: str) -> dict[str, Any] | None:
    """Agent calls the customer; the call fetches TwiML from voice_url."""
    s = get_settings()
    if not is_configured() or not s.twilio_from_number:
        return None
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(
            f"{_API}/Accounts/{s.twilio_account_sid}/Calls.json",
            auth=(s.twilio_account_sid, s.twilio_auth_token),
            data={"To": to, "From": s.twilio_from_number, "Url": voice_url},
        )
        return r.json() if r.status_code in (200, 201) else None
