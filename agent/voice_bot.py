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
    "customer. Keep replies short and spoken-friendly. Ask one clarifying question if "
    "needed. The moment the user describes a concrete bug or broken behavior, say "
    "exactly 'On it, give me a moment' and immediately call fix_connected_repo with a "
    "clear one-line symptom. Do NOT say anything else while it runs. When it returns, "
    "say in one sentence what you fixed and that the preview and PR links are in the "
    "chat. Never read out URLs."
)

FIX_SCHEMA = FunctionSchema(
    name="fix_connected_repo",
    description="Fix a concrete bug in the connected repo. Builds a preview + opens a PR.",
    properties={"symptom": {"type": "string", "description": "The concrete bug, in one line."}},
    required=["symptom"],
)


async def run_bot(room_url: str, token: str, *, brand_slug: str = "",
                  repo_url: str = "", github_token: str = "") -> None:
    """Join the Daily room and run the voice + FDE agent until the room empties."""
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

    async def do_fix(params: Any) -> None:
        symptom = (params.arguments or {}).get("symptom", "the reported issue")
        await _chat(f"🔧 On it. Building a fix for: {symptom}")
        from app.fde.repo_sandbox import fix_connected_repo

        res = await fix_connected_repo(repo_url, symptom, token=github_token)
        if res.get("error"):
            await _chat(f"⚠ {res['error']} (connect GitHub in Settings to fix this repo)")
            await params.result_callback({"error": res["error"]})
            return
        # Post preview + PR into the call chat so the user can open them right there.
        links = []
        if res.get("preview_url"):
            links.append(f"✅ Preview (safe, prod untouched): {res['preview_url']}")
        if res.get("pr_url"):
            links.append(f"🔀 PR: {res['pr_url']}")
        if not links:
            links.append("Diff ready. add a GitHub token in Settings to open the PR + preview.")
        await _chat("\n".join(links))
        await params.result_callback({
            "explanation": res.get("explanation") or "done",
            "preview_url": res.get("preview_url"),
            "pr_url": res.get("pr_url"),
            "spoke_links": "I dropped the preview and PR in the chat",
        })

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
    async def _greet(_t, _p):  # noqa: ANN001
        await task.queue_frames([
            TTSSpeakFrame("Hi, I'm on. Show me or tell me what's broken."),
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
