"""TwoCustomer agent — FastAPI control plane.

Hosts the Claude tool loop, the monitor scheduler, the FDE sandbox, and the
channel routes (Discord, Deepgram voice, Twilio, Daily). A deterministic stub
LLM backs the tests and offline dev so the full web->agent->stream path runs
without any API key; the real Claude client is used whenever a key is present.
"""

from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.channels import daily, deepgram, discord, slack, twilio

from app import observability as obs
from app.config import get_settings
from app.core.loop import run_agent
from app.llm.base import LLMClient
from app.llm.stub import StubLLM
from app.state import history
from app.tools import echo  # noqa: F401 - registers the echo tool
from app.tools import memory_tool  # noqa: F401 - registers recall_memory
from app.tools import campaign_tool  # noqa: F401 - registers create_campaign
from app.tools import edit_copy  # noqa: F401 - registers edit_copy
from app.tools import edit_image  # noqa: F401 - registers edit_product_image
from app.tools import fix_site_tool  # noqa: F401 - registers fix_site
from app.tools import monitor_tool  # noqa: F401 - registers monitor_brand
from app.tools import propose_fix  # noqa: F401 - registers propose_fix
from app.tools import video_tool  # noqa: F401 - registers start_video_session
from app.tools.registry import registry

settings = get_settings()
obs.init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # The background monitor scheduler only runs on a long-lived host. On
    # serverless (Vercel), skip it — request endpoints still work, and the
    # monitor cadence runs from a real always-on deployment.
    serverless = bool(os.environ.get("VERCEL"))
    sched = None
    if not serverless:
        from app.monitor.scheduler import build_scheduler

        sched = build_scheduler()
        sched.start()
        app.state.scheduler = sched
    # repopulate the scheduler with persisted monitor configs (survive restart)
    try:
        from app.monitor.config import all_configs
        from app.monitor.scheduler import REGISTERED

        for cfg in await all_configs():
            REGISTERED[cfg.brand_slug] = cfg.model_dump()
    except Exception:  # noqa: BLE001
        pass
    try:
        yield
    finally:
        if sched is not None:
            sched.shutdown(wait=False)


# On serverless (Vercel), skip the lifespan entirely — its only jobs are the
# background scheduler (not viable serverless) and config preload. Vercel's ASGI
# wrapper is also unreliable with the lifespan protocol.
_LIFESPAN = None if os.environ.get("VERCEL") else lifespan
app = FastAPI(title="TwoCustomer Agent", version="0.1.0", lifespan=_LIFESPAN)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agent-facing endpoints require AGENT_SHARED_TOKEN *when it is configured*.
# Webhooks (/slack, /twilio, /discord) use their own signature verification and
# are excluded. /health, /assets, /sentry-debug stay open.
_PROTECTED = ("/chat", "/interview", "/session/video", "/fde/fix", "/fde/github",
              "/edit/image", "/monitor/config")


@app.middleware("http")
async def _agent_token_guard(request: Request, call_next):
    tok = settings.shared_token
    if tok and any(request.url.path.startswith(p) for p in _PROTECTED):
        if request.headers.get("authorization", "") != f"Bearer {tok}":
            return Response(status_code=401, content="unauthorized")
    return await call_next(request)


def get_llm() -> LLMClient:
    """Return the active LLM. Claude when keyed; stub when forced or unkeyed."""
    import os

    if os.environ.get("FORCE_STUB") == "1":
        return StubLLM()
    if settings.has_anthropic():
        try:
            from app.llm.claude import ClaudeLLM  # lazy: only if P2 present

            return ClaudeLLM()
        except Exception:
            pass
    return StubLLM()


@app.get("/sentry-debug")
async def sentry_debug() -> dict[str, Any]:
    """Trigger a test error so you can confirm Sentry capture (then check Issues)."""
    _ = 1 / 0  # noqa: F841 - intentional, captured by Sentry
    return {"ok": True}  # unreachable


@app.get("/assets/{asset_id}")
async def get_asset(asset_id: str) -> Response:
    """Serve AI-generated/edited images produced by edit_product_image."""
    aid = asset_id.rsplit(".", 1)[0]
    item = edit_image.ASSETS.get(aid)
    if not item:
        return Response(status_code=404)
    mime, data = item
    return Response(content=data, media_type=mime)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "twocustomer-agent",
        "llm": "claude" if settings.has_anthropic() else "stub",
        "convex": settings.has_convex(),
        "redis": settings.has_redis(),
        "browserbase": settings.has_browserbase(),
        "gemini": settings.has_gemini(),
        "daily": daily.is_configured(),
        "deepgram": bool(settings.deepgram_api_key),
        "discord": bool(settings.discord_bot_token),
        "twilio": bool(settings.twilio_account_sid and settings.twilio_auth_token),
        "tools": registry.names(),
    }


class ChatRequest(BaseModel):
    message: str
    participant: str = "web-user"
    history: list[dict[str, str]] = []


class MonitorConfigBody(BaseModel):
    brand_slug: str
    terms: list[str] = []
    interval_minutes: int = 30
    threshold: float = 0.7
    enabled: bool = True


class TwilioCallBody(BaseModel):
    to: str


_PROMPT_PATH = Path(__file__).parent / "llm" / "prompt_twocustomer.md"
try:
    SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")
except OSError:
    SYSTEM_PROMPT = "You are TwoCustomer, an always-on AI analyst for a consumer brand."


@app.post("/chat")
async def chat(req: ChatRequest) -> EventSourceResponse:
    """Stream the agent's reply as SSE events: token / tool_start / tool_end / done."""
    messages: list[dict[str, Any]] = [
        {"role": "user" if h.get("role") != "assistant" else "assistant",
         "content": h.get("content", "")}
        for h in req.history
    ]
    messages.append({"role": "user", "content": req.message})

    async def event_gen():
        from app.state.limits import allow

        if not await allow(f"chat:{req.participant}", limit=60, window_s=60):
            yield {"event": "error",
                   "data": json.dumps({"error": "Rate limit — slow down a moment."})}
            yield {"event": "message",
                   "data": json.dumps({"text": "⚠ Rate limit — give it a sec.", "rounds": 0})}
            yield {"event": "done", "data": "{}"}
            return
        llm = get_llm()
        await history.append(req.participant, "user", req.message)

        # Run the agent in the background; stream its progress events live so the
        # UI shows tool activity immediately instead of a frozen spinner.
        queue: asyncio.Queue = asyncio.Queue()

        async def on_event(ev: str, data: dict[str, Any]) -> None:
            await queue.put((ev, data))

        async def run() -> None:
            try:
                with obs.Timer() as t:
                    res = await run_agent(
                        llm=llm, registry=registry, system=SYSTEM_PROMPT,
                        messages=messages, context={"participant": req.participant},
                        on_event=on_event,
                    )
                obs.trace_agent_run(
                    participant=req.participant, rounds=res.rounds,
                    tools=[e["name"] for e in res.tool_log], duration_ms=t.ms,
                )
                await queue.put(("__done__", res))
            except Exception as exc:  # noqa: BLE001 - surface to UI, never 500
                obs.capture(exc)
                await queue.put(("__error__", exc))

        task = asyncio.create_task(run())
        result = None
        error = None
        while True:
            ev, data = await queue.get()
            if ev == "__done__":
                result = data
                break
            if ev == "__error__":
                error = data
                break
            out = dict(data)
            if ev == "tool_end" and isinstance(out.get("output"), str):
                out["output"] = out["output"][:400]
            yield {"event": ev, "data": json.dumps(out)}

        if error is not None:
            msg = str(error)
            hint = ("Anthropic credit balance is too low — add credits or set a "
                    "funded ANTHROPIC_API_KEY." if "credit balance" in msg else msg)
            yield {"event": "error", "data": json.dumps({"error": hint})}
            yield {"event": "message",
                   "data": json.dumps({"text": f"⚠ {hint}", "rounds": 0})}
            yield {"event": "done", "data": "{}"}
            return

        # Surface artifacts (packet / generated image) from the tool log.
        for entry in result.tool_log:
            if entry["name"] == "propose_fix":
                yield {"event": "artifact",
                       "data": json.dumps({"kind": "packet", "text": entry["output"]})}
            if entry["name"] == "edit_product_image" and "/assets/" in entry["output"]:
                url = entry["output"].split("/assets/", 1)[1].split(" ", 1)[0]
                yield {"event": "artifact",
                       "data": json.dumps({"kind": "image", "url": f"/assets/{url}"})}

        # Always send a final message so the chat is never blank.
        text = result.text or (
            "Done. Tell me a specific action — monitor a brand, build a campaign, "
            "fix a site, or edit an image — and I'll run it."
        )
        await history.append(req.participant, "assistant", text)
        for word in text.split(" "):
            yield {"event": "token", "data": json.dumps({"text": word + " "})}
        yield {"event": "message",
               "data": json.dumps({"text": text, "rounds": result.rounds})}
        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(event_gen())


# ── Slack channel ─────────────────────────────────────────────────────────────

async def _run_text(message: str, participant: str) -> str:
    """Run the agent loop once and return final text (used by Slack/voice)."""
    from app.core.loop import run_agent

    result = await run_agent(
        llm=get_llm(), registry=registry, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": message}],
        context={"participant": participant},
    )
    return result.text


@app.post("/slack/events")
async def slack_events(request: Request) -> Any:
    body = (await request.body()).decode()
    payload = json.loads(body or "{}")
    # URL verification handshake — echo the challenge.
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge")}
    # Verify signature for real events.
    if not slack.verify_signature(
        signing_secret=settings.slack_signing_secret,
        timestamp=request.headers.get("X-Slack-Request-Timestamp", ""),
        body=body,
        signature=request.headers.get("X-Slack-Signature", ""),
    ):
        return Response(status_code=401)
    event = payload.get("event", {})
    if event.get("type") in ("app_mention", "message") and not event.get("bot_id"):
        text = event.get("text", "")
        reply = await _run_text(text, participant=f"slack:{event.get('user','')}")
        await slack.post_message(event.get("channel", ""), reply)
    return {"ok": True}


@app.post("/slack/command")
async def slack_command(request: Request) -> Any:
    raw = (await request.body()).decode()
    if not slack.verify_signature(
        signing_secret=settings.slack_signing_secret,
        timestamp=request.headers.get("X-Slack-Request-Timestamp", ""),
        body=raw,
        signature=request.headers.get("X-Slack-Signature", ""),
    ):
        return Response(status_code=401)
    from urllib.parse import parse_qs

    text = (parse_qs(raw).get("text", [""])[0])
    reply = await _run_text(text, participant="slack:slash")
    return {"response_type": "in_channel", "text": reply}


# ── Monitor config ────────────────────────────────────────────────────────────

@app.get("/monitor/config/{slug}")
async def monitor_config_get(slug: str) -> dict[str, Any]:
    from app.monitor.config import get_config

    cfg = await get_config(slug)
    return {"config": cfg.model_dump() if cfg else None}


@app.post("/monitor/config")
async def monitor_config_set(cfg: "MonitorConfigBody") -> dict[str, Any]:
    from app.monitor.config import MonitorConfig, save_config
    from app.monitor.scheduler import REGISTERED

    saved = await save_config(MonitorConfig(**cfg.model_dump()))
    REGISTERED[saved.brand_slug] = saved.model_dump()  # arm the scheduler
    return {"config": saved.model_dump()}


# ── Discord channel (free Slack alternative) ──────────────────────────────────

@app.post("/discord/interactions")
async def discord_interactions(request: Request) -> Any:
    body = (await request.body()).decode()
    if not discord.verify_signature(
        public_key=settings.discord_public_key,
        signature=request.headers.get("X-Signature-Ed25519", ""),
        timestamp=request.headers.get("X-Signature-Timestamp", ""),
        body=body,
    ):
        return Response(status_code=401)
    payload = json.loads(body or "{}")
    itype = payload.get("type")
    if itype == discord.PING:
        return {"type": discord.PONG}
    if itype == discord.APPLICATION_COMMAND:
        text = discord.command_text(payload)
        token = payload.get("token", "")

        async def _work() -> None:
            reply = await _run_text(text, participant="discord")
            await discord.followup(token, reply)

        asyncio.create_task(_work())  # answer within 3s, deliver via followup
        return {"type": discord.DEFERRED_MESSAGE}
    return {"type": discord.PONG}


# ── Customer interview ────────────────────────────────────────────────────────

class InterviewStart(BaseModel):
    session_id: str
    brand: str = "aurora-drinks"
    customer: str = "Customer"


class InterviewAnswer(BaseModel):
    session_id: str
    text: str


@app.post("/interview/start")
async def interview_start(req: InterviewStart) -> dict[str, Any]:
    from app.interview.fsm import Interview
    from app.state.limits import session_set

    iv = Interview(brand=req.brand, customer=req.customer)
    question = iv.start()
    await session_set(req.session_id, iv.__dict__)
    return {"question": question, "done": False, "progress": list(iv.progress())}


@app.post("/interview/answer")
async def interview_answer(req: InterviewAnswer) -> dict[str, Any]:
    from app.interview.fsm import Interview
    from app.interview.synth import synth_session
    from app.state.limits import session_get, session_set

    state = await session_get(req.session_id)
    if not state:
        return {"error": "no such session"}
    iv = Interview(**state)
    nxt = iv.answer(req.text)
    await session_set(req.session_id, iv.__dict__)
    if iv.done:
        insight = await synth_session(iv)
        return {"question": None, "done": True, "insight": insight}
    return {"question": nxt, "done": False, "progress": list(iv.progress())}


# ── Direct capability endpoints (for the web UI panels) ───────────────────────

class EditImageBody(BaseModel):
    instruction: str
    image_url: str | None = None


@app.post("/edit/image")
async def edit_image_ep(req: EditImageBody) -> dict[str, Any]:
    out = await edit_image.edit_product_image(req.instruction, req.image_url)
    url = None
    if "/assets/" in out:
        url = "/assets/" + out.split("/assets/", 1)[1].split(" ", 1)[0]
    # data_url renders inline in the UI — no second /assets request (serverless-safe).
    return {"message": out, "url": url, "data_url": edit_image.data_url_for(url)}


class FixBody(BaseModel):
    symptom: str = "homepage hero renders 'hi hi my my'"


@app.post("/fde/fix")
async def fde_fix_ep(req: FixBody) -> dict[str, Any]:
    from app.fde.sandbox import fix_site

    if not settings.has_anthropic():
        return {"error": "ANTHROPIC_API_KEY not set", "resolved": False}
    return await fix_site(req.symptom)


@app.get("/discord/context")
async def discord_context(channel_id: str | None = None, limit: int = 20) -> dict[str, Any]:
    """Recent messages from the team's Discord channel, as context text."""
    text = await discord.read_context(channel_id, limit=limit)
    return {"context": text, "configured": bool(settings.discord_channel_id or channel_id)}


class GithubFixBody(BaseModel):
    repo_url: str
    symptom: str
    context: str = ""


@app.post("/fde/github")
async def fde_github_ep(req: GithubFixBody) -> dict[str, Any]:
    """Clone a public GitHub repo, diagnose + patch the bug, open a PR / return
    a diff. Pulls extra context (Discord + web monitoring) when provided."""
    from app.fde.github import fix_github

    if not settings.has_anthropic():
        return {"error": "ANTHROPIC_API_KEY not set"}
    return await fix_github(req.repo_url, req.symptom, context=req.context)


# ── Daily video + screen-share session ────────────────────────────────────────

@app.post("/session/video")
async def session_video() -> dict[str, Any]:
    room = await daily.create_room()
    if not room:
        return {"error": "DAILY_API_KEY not set", "room_url": None}
    owner = await daily.meeting_token(room["name"], is_owner=True, user_name="TwoCustomer")
    return {"room_url": room["url"], "name": room["name"], "owner_token": owner,
            "screenshare": True}


# ── Twilio channel (SMS + phone-call interviews) ──────────────────────────────

async def _interview_step(session_id: str, answer: str | None,
                          brand: str = "your brand", customer: str = "Customer") -> dict:
    """Advance (or start) a phone/SMS interview keyed by phone number."""
    from app.interview.fsm import Interview
    from app.interview.synth import synth_session
    from app.state.limits import session_get, session_set

    state = await session_get(session_id)
    if not state:
        iv = Interview(brand=brand, customer=customer)
        q = iv.start()
        await session_set(session_id, iv.__dict__)
        return {"question": q, "done": False}
    iv = Interview(**state)
    nxt = iv.answer(answer or "")
    await session_set(session_id, iv.__dict__)
    if iv.done:
        await synth_session(iv, channel="phone")
        return {"question": None, "done": True}
    return {"question": nxt, "done": False}


@app.post("/twilio/sms")
async def twilio_sms(request: Request) -> Response:
    form = dict(await request.form())
    if not twilio.verify_signature(
        auth_token=settings.twilio_auth_token,
        signature=request.headers.get("X-Twilio-Signature", ""),
        url=str(request.url), params={k: str(v) for k, v in form.items()},
    ):
        return Response(status_code=403)
    frm, body = str(form.get("From", "")), str(form.get("Body", ""))
    step = await _interview_step(f"sms:{frm}", body or None)
    msg = (step["question"] if not step["done"]
           else "Thank you — that's all. Your feedback just went to the team. 💚")
    return Response(twilio.twiml_message(msg), media_type="application/xml")


def _external_url(request: Request) -> str:
    """Reconstruct the public URL Twilio actually called (so the HMAC matches
    behind a tunnel/proxy, where request.url is the internal localhost URL)."""
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if not host:
        return str(request.url)
    q = f"?{request.url.query}" if request.url.query else ""
    return f"{proto}://{host}{request.url.path}{q}"


def _twilio_verified(request: Request, form: dict) -> bool:
    return twilio.verify_signature(
        auth_token=settings.twilio_auth_token,
        signature=request.headers.get("X-Twilio-Signature", ""),
        url=_external_url(request), params={k: str(v) for k, v in form.items()})


@app.post("/twilio/voice")
async def twilio_voice(request: Request) -> Response:
    form = dict(await request.form())
    if not _twilio_verified(request, form):
        return Response(status_code=403)
    frm = str(form.get("From", "anon"))
    step = await _interview_step(f"call:{frm}", None)
    twiml = twilio.twiml_say_gather(
        "Hi, this is TwoCustomer calling on behalf of the brand. " + (step["question"] or ""),
        action=f"{settings.agent_base_url}/twilio/voice/gather")
    return Response(twiml, media_type="application/xml")


@app.post("/twilio/voice/gather")
async def twilio_voice_gather(request: Request) -> Response:
    form = dict(await request.form())
    if not _twilio_verified(request, form):
        return Response(status_code=403)
    frm = str(form.get("From", "anon"))
    speech = str(form.get("SpeechResult", ""))
    step = await _interview_step(f"call:{frm}", speech)
    if step["done"]:
        twiml = twilio.twiml_say_gather(
            "Thank you so much, that's really helpful. Goodbye!",
            action="", end=True)
    else:
        twiml = twilio.twiml_say_gather(
            step["question"] or "",
            action=f"{settings.agent_base_url}/twilio/voice/gather")
    return Response(twiml, media_type="application/xml")


@app.post("/twilio/call")
async def twilio_call(req: TwilioCallBody) -> dict[str, Any]:
    res = await twilio.place_call(req.to, voice_url=f"{settings.agent_base_url}/twilio/voice")
    return {"placed": bool(res), "sid": (res or {}).get("sid")}


# ── Voice channel (Deepgram) ──────────────────────────────────────────────────

@app.post("/voice/transcribe")
async def voice_transcribe(request: Request) -> Response:
    if not deepgram.is_configured():
        return Response(json.dumps({"transcript": "",
                                    "error": "DEEPGRAM_API_KEY not set"}),
                        status_code=503, media_type="application/json")
    audio = await request.body()
    ctype = request.headers.get("Content-Type", "audio/wav")
    try:
        text = await deepgram.transcribe(audio, content_type=ctype)
    except Exception as exc:  # noqa: BLE001
        return Response(json.dumps({"transcript": "", "error": str(exc)}),
                        status_code=502, media_type="application/json")
    return Response(json.dumps({"transcript": text}),
                    media_type="application/json")


@app.post("/voice/speak")
async def voice_speak(req: ChatRequest) -> Response:
    if not deepgram.is_configured():
        return Response(json.dumps({"error": "DEEPGRAM_API_KEY not set"}),
                        status_code=503, media_type="application/json")
    try:
        audio = await deepgram.synthesize(req.message)
    except Exception as exc:  # noqa: BLE001
        return Response(json.dumps({"error": str(exc)}),
                        status_code=502, media_type="application/json")
    return Response(content=audio, media_type="audio/mpeg")
