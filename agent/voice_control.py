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


@app.post("/join")
async def join(req: JoinBody, request: Request) -> Any:
    if not _authed(request):
        return Response(status_code=401)
    if req.room_url in _SESSIONS and not _SESSIONS[req.room_url].done():
        return {"ok": True, "note": "already joined"}

    async def _run() -> None:
        try:
            await run_bot(req.room_url, req.token, brand_slug=req.brand_slug,
                          repo_url=req.repo_url, github_token=req.github_token)
        except Exception as exc:  # noqa: BLE001
            from loguru import logger
            logger.warning(f"voice session ended with error: {exc}")
        finally:
            _SESSIONS.pop(req.room_url, None)

    _SESSIONS[req.room_url] = asyncio.create_task(_run())
    return {"ok": True}


@app.post("/leave")
async def leave(req: JoinBody, request: Request) -> Any:
    if not _authed(request):
        return Response(status_code=401)
    t = _SESSIONS.pop(req.room_url, None)
    if t and not t.done():
        t.cancel()
    return {"ok": True}
