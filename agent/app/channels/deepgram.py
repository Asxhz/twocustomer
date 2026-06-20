"""Deepgram voice — STT + TTS for the customer-interview channel.

REST clients (prerecorded STT + TTS). Streaming STT (WS) is wired by the web
voice page. No-ops cleanly when DEEPGRAM_API_KEY is unset.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings

_LISTEN = "https://api.deepgram.com/v1/listen"
_SPEAK = "https://api.deepgram.com/v1/speak"


def is_configured() -> bool:
    return bool(get_settings().deepgram_api_key)


def _auth() -> dict[str, str]:
    return {"Authorization": f"Token {get_settings().deepgram_api_key}"}


async def transcribe(audio: bytes, *, content_type: str = "audio/wav",
                     model: str = "nova-3") -> str:
    """Transcribe prerecorded audio. Returns the transcript text."""
    if not is_configured():
        raise RuntimeError("DEEPGRAM_API_KEY not set")
    params = {"model": model, "smart_format": "true", "punctuate": "true"}
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            _LISTEN, params=params,
            headers={**_auth(), "Content-Type": content_type},
            content=audio,
        )
        r.raise_for_status()
        data: dict[str, Any] = r.json()
    try:
        return data["results"]["channels"][0]["alternatives"][0]["transcript"]
    except (KeyError, IndexError):
        return ""


async def synthesize(text: str, *, model: str = "aura-2-thalia-en") -> bytes:
    """Text → speech audio bytes (mp3)."""
    if not is_configured():
        raise RuntimeError("DEEPGRAM_API_KEY not set")
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            _SPEAK, params={"model": model},
            headers={**_auth(), "Content-Type": "application/json"},
            json={"text": text},
        )
        r.raise_for_status()
        return r.content


def stream_stt_url(*, model: str = "nova-3") -> str:
    """WSS URL the browser uses for live streaming STT (token sent as subprotocol)."""
    return f"wss://api.deepgram.com/v1/listen?model={model}&smart_format=true"
