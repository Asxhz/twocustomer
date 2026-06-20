"""Daily video + screen-share live sessions.

A live interview/working session where the customer and the agent join a WebRTC
room — with **screen share** so the customer can show their broken site while
the agent (and admin) watch and interview. Rooms are created via Daily's REST
API; the web app embeds the room with Daily Prebuilt.

Separate from Discord voice and Twilio phone — this is the rich video surface.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.config import get_settings

_API = "https://api.daily.co/v1"


def is_configured() -> bool:
    return bool(get_settings().daily_api_key)


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {get_settings().daily_api_key}",
            "Content-Type": "application/json"}


async def create_room(*, name: str | None = None, ttl_seconds: int = 3600) -> dict[str, Any] | None:
    """Create a Daily room with screen-share + chat enabled. Returns {name,url}."""
    if not is_configured():
        return None
    props: dict[str, Any] = {
        "enable_screenshare": True,
        "enable_chat": True,
        "start_video_off": False,
        "start_audio_off": False,
        "exp": int(time.time()) + ttl_seconds,
    }
    body: dict[str, Any] = {"properties": props}
    if name:
        body["name"] = name
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(f"{_API}/rooms", headers=_headers(), json=body)
        if r.status_code not in (200, 201):
            return None
        d = r.json()
    return {"name": d.get("name"), "url": d.get("url")}


async def meeting_token(room_name: str, *, is_owner: bool = False,
                        user_name: str = "guest") -> str | None:
    """Mint a meeting token for a room (owner = agent/admin controls)."""
    if not is_configured():
        return None
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(f"{_API}/meeting-tokens", headers=_headers(),
                         json={"properties": {"room_name": room_name,
                                              "is_owner": is_owner,
                                              "user_name": user_name}})
        return r.json().get("token") if r.status_code in (200, 201) else None
