"""Local control server for the Pipecat voice agent (port 8100).

The agent service (or anything with the shared token) calls POST /join with a Daily
room + the project's repo/token, and a voice-agent session joins that room. Real-time
media, so this is a long-running local process (not Vercel). Run:

    agent/.venv/bin/python -m uvicorn voice_control:app --port 8100
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

from app.config import get_settings
from voice_bot import run_bot

S = get_settings()
app = FastAPI(title="TwoCustomer Voice Control")
_SESSIONS: dict[str, asyncio.Task] = {}


def _authed(request: Request) -> bool:
    if not S.shared_token:
        return True
    return request.headers.get("Authorization", "") == f"Bearer {S.shared_token}"


class JoinBody(BaseModel):
    room_url: str
    token: str = ""
    brand_slug: str = ""
    repo_url: str = ""
    github_token: str = ""


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "active_calls": list(_SESSIONS.keys())}


def _spawn(room_url: str, token: str, brand: str, repo: str, gh: str,
           announce: str = "", preview_url: str = "", pr_url: str = "") -> None:
    """Start (or restart) a voice session in a room. `announce` marks a rejoin
    session that returns after building a change. A `rejoin` callback is wired in
    so the agent can leave to build, then come back, repeatedly."""

    async def _rejoin(announce_text: str, res: dict) -> None:
        # Small gap so the previous session has fully left the room.
        await asyncio.sleep(1.0)
        _spawn(room_url, token, brand, repo, gh, announce=announce_text,
               preview_url=res.get("preview_url") or "", pr_url=res.get("pr_url") or "")

    async def _run() -> None:
        try:
            await run_bot(room_url, token, brand_slug=brand, repo_url=repo,
                          github_token=gh, announce=announce, rejoin=_rejoin,
                          preview_url=preview_url, pr_url=pr_url)
        except Exception as exc:  # noqa: BLE001
            from loguru import logger
            logger.warning(f"voice session ended with error: {exc}")
        finally:
            # Only clear the slot if this task is still the current one (a rejoin
            # may have replaced it).
            if _SESSIONS.get(room_url) is cur:
                _SESSIONS.pop(room_url, None)

    cur = asyncio.create_task(_run())
    _SESSIONS[room_url] = cur


@app.post("/join")
async def join(req: JoinBody, request: Request) -> Any:
    if not _authed(request):
        return Response(status_code=401)
    if req.room_url in _SESSIONS and not _SESSIONS[req.room_url].done():
        return {"ok": True, "note": "already joined"}
    _spawn(req.room_url, req.token, req.brand_slug, req.repo_url, req.github_token)
    return {"ok": True}


@app.post("/leave")
async def leave(req: JoinBody, request: Request) -> Any:
    if not _authed(request):
        return Response(status_code=401)
    t = _SESSIONS.pop(req.room_url, None)
    if t and not t.done():
        t.cancel()
    return {"ok": True}
