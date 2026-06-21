"""TwoCustomer voice agent: joins a Daily room, talks, listens, and builds.

Pipecat pipeline: Daily audio in -> Silero VAD -> Deepgram STT -> Claude (with a
fix_connected_repo function tool) -> Deepgram Aura TTS -> Daily audio out.
Barge-in (interruptions) on. When the user describes a concrete bug, Claude calls
fix_connected_repo on the project's repo; the agent speaks the result and posts the
preview + PR link into the call chat. Real-time, so this runs as a local process.
"""

from __future__ import annotations

import asyncio
from typing import Any

from loguru import logger

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import EndFrame, LLMRunFrame, TTSSpeakFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.services.anthropic.llm import AnthropicLLMService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.deepgram.tts import DeepgramTTSService
from pipecat.transports.daily.transport import DailyParams, DailyTransport

from app.config import get_settings
from app.llm.router import model_for

S = get_settings()

SYSTEM = (
    "You are TwoCustomer, a forward-deployed engineer on a live video call with a "
    "customer. You can SEE the user's shared screen (images are attached) and hear "
    "them. Keep replies short and spoken-friendly. Use what you see and hear. "
    "The user can ask for ANY change — fix a bug, change colors or fonts, edit copy, "
    "or tweak layout. The moment you understand a concrete change they want, say "
    "exactly: 'On it — give me a moment, I'll stop listening and be right back.' "
    "Then immediately call fix_connected_repo with a clear one-line description of the "
    "change. Do NOT say anything else while it runs. When it returns, say 'Okay, I'm "
    "back —' then in one sentence what you changed and that the live preview link is in "
    "the chat. If they ask for another change, do it again. Never read out URLs."
)

FIX_SCHEMA = FunctionSchema(
    name="fix_connected_repo",
    description=("Apply a change to the connected repo and ship a live preview — a bug "
                 "fix, a color/font/style change, a copy edit, or a layout tweak. "
                 "Builds a live preview and opens/updates a PR."),
    properties={"symptom": {"type": "string",
                            "description": "The concrete change to make, in one line."}},
    required=["symptom"],
)


# Detached handoff tasks (FDE build + rejoin) must outlive the pipeline that
# spawned them, so we keep hard references here until they finish.
_PENDING: set[asyncio.Task] = set()


async def run_bot(room_url: str, token: str, *, brand_slug: str = "",
                  repo_url: str = "", github_token: str = "",
                  announce: str = "", rejoin=None,
                  preview_url: str = "", pr_url: str = "") -> None:
    """Join the Daily room and run the voice + FDE agent until the room empties.

    announce: if set, the agent speaks this on join instead of the generic greeting
      (used by a rejoin session that returns after building a change).
    rejoin: async callable(announce_text) that starts a fresh session in the same
      room. The agent leaves while it builds, then calls this to come back.
    """
    transport = DailyTransport(
        room_url, token, "TwoCustomer",
        DailyParams(
            audio_in_enabled=True,
            audio_in_sample_rate=16000,
            audio_out_enabled=True,
            # Match the TTS rate exactly, or the voice plays low/slow.
            audio_out_sample_rate=24000,
            video_in_enabled=True,  # receive the screen-share track
            vad_analyzer=SileroVADAnalyzer(),
        ),
    )
    stt = DeepgramSTTService(api_key=S.deepgram_api_key, sample_rate=16000)
    tts = DeepgramTTSService(api_key=S.deepgram_api_key, voice="aura-2-thalia-en",
                             sample_rate=24000)
    # Sonnet on the call: far more reliable at deciding to call the fix tool.
    from app.llm.router import SONNET

    llm = AnthropicLLMService(api_key=S.anthropic_api_key, model=SONNET)

    async def _chat(text: str) -> None:
        try:
            await transport.send_prebuilt_chat_message(text, "TwoCustomer")
        except Exception:  # noqa: BLE001
            pass

    # Track whether we've already made a change on this call, so follow-up
    # requests stack on the same working branch + preview (the "keep editing" loop).
    state = {"iterated": False}

    async def _handoff(symptom: str) -> None:
        """Runs detached after the agent leaves: build the change, record the link,
        then rejoin the room and announce it. Survives the pipeline teardown."""
        from app.fde.repo_sandbox import fix_connected_repo

        try:
            res = await fix_connected_repo(repo_url, symptom, token=github_token,
                                           iterate=state["iterated"])
        except Exception as exc:  # noqa: BLE001
            res = {"error": str(exc)}
        if not res.get("error"):
            state["iterated"] = True
            try:
                from app.state.call_links import record_link

                await record_link(room_url, res)
            except Exception:  # noqa: BLE001
                pass

        if res.get("error"):
            announce_text = (f"I am back. I could not make that change: {res['error']}. "
                             "Tell me again and I will retry.")
        else:
            has_pr = bool(res.get("pr_url"))
            guide = ("I opened a pull request and built a live preview. "
                     "Check the pull request on GitHub and open the preview on Vercel. "
                     "Both links are in the chat." if has_pr else
                     "I built a live preview. Open the preview link in the chat to check it.")
            announce_text = ("I am back. I found the issue and fixed it. "
                             + (res.get("explanation") or "") + " " + guide)
        # Rejoin the same room with the result. If rejoin is unavailable, the link
        # is still recorded for the UI panel, so nothing is lost.
        if rejoin is not None:
            try:
                await rejoin(announce_text, res)
            except Exception:  # noqa: BLE001
                pass

    async def do_fix(params: Any) -> None:
        symptom = (params.arguments or {}).get("symptom", "the reported change")
        await _chat(f"On it: {symptom}. Stepping off to build it, back in a moment.")
        # Detach the build+rejoin so it outlives this pipeline, then leave the call.
        fut = asyncio.ensure_future(_handoff(symptom))
        _PENDING.add(fut)
        fut.add_done_callback(_PENDING.discard)
        await params.result_callback({"status": "working",
                                      "note": "stepping off the call to build; will rejoin"})
        await task.queue_frame(EndFrame())

    llm.register_function("fix_connected_repo", do_fix)

    context = LLMContext(
        messages=[{"role": "system", "content": SYSTEM}],
        tools=ToolsSchema(standard_tools=[FIX_SCHEMA]),
    )
    pair = LLMContextAggregatorPair(context)

    pipeline = Pipeline([
        transport.input(),
        stt,
        pair.user(),
        llm,
        tts,
        transport.output(),
        pair.assistant(),
    ])
    task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))

    @transport.event_handler("on_first_participant_joined")
    async def _greet(_t, participant):  # noqa: ANN001
        # Watch the participant's screen-share so Claude can see what they show.
        pid = participant.get("id") if isinstance(participant, dict) else getattr(participant, "id", None)
        if pid:
            for source in ("screenVideo", "camera"):
                try:
                    await transport.capture_participant_video(pid, framerate=1, video_source=source)
                except Exception:  # noqa: BLE001
                    pass
        if announce:
            # Rejoin session: post the link, speak the result, then keep listening.
            links = []
            if pr_url:
                links.append(f"Pull request (GitHub): {pr_url}")
            if preview_url:
                links.append(f"Live preview (Vercel): {preview_url}")
            if links:
                links.append("Open these to review the fix. Production was not touched.")
                await _chat("\n".join(links))
            await task.queue_frames([TTSSpeakFrame(announce), LLMRunFrame()])
        else:
            await task.queue_frames([
                TTSSpeakFrame("Hi, I'm on and watching your screen. Tell me what you'd "
                              "like changed, or show me what's off."),
                LLMRunFrame(),
            ])

    @transport.event_handler("on_participant_left")
    async def _maybe_end(_t, _p, _reason):  # noqa: ANN001
        counts = transport.participant_counts() if hasattr(transport, "participant_counts") else {}
        if isinstance(counts, dict) and counts.get("present", 0) <= 1:
            await task.queue_frame(EndFrame())

    logger.info(f"voice agent joining {room_url} (brand={brand_slug}, repo={repo_url})")
    await PipelineRunner(handle_sigint=False).run(task)
    logger.info("voice agent left the call")
