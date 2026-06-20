"""Thin client from the uAgent to the TwoCustomer control plane (agent/ FastAPI).

Forwards a parsed Intent to the right endpoint and returns a short text reply
suitable for an ASI:One chat response.
"""

from __future__ import annotations

import json
import os

import httpx

from intent import Intent

AGENT_BASE_URL = os.environ.get("AGENT_BASE_URL", "http://localhost:8000")
SHARED_TOKEN = os.environ.get("AGENT_SHARED_TOKEN", "")


def _headers() -> dict[str, str]:
    h = {"Content-Type": "application/json"}
    if SHARED_TOKEN:
        h["Authorization"] = f"Bearer {SHARED_TOKEN}"
    return h


async def handle(intent: Intent) -> str:
    """Route an intent to the control plane. Returns a chat-ready string."""
    if intent.action == "help":
        return ("I'm TwoCustomer — your brand's AI analyst. Ask me to: "
                "`monitor <brand>`, `campaign <brief>`, `interview customers`, "
                "`insights`, or `status`.")
    if intent.action == "status":
        return await _get_health()

    # monitor / campaign / interview / insights → drive the chat agent with a
    # directive so the existing Claude tool-loop does the work.
    directive = {
        "monitor": f"Monitor the brand '{intent.arg}'. Start tracking and report what you find.",
        "campaign": f"Build a marketing campaign: {intent.arg}",
        "interview": f"Set up a customer interview about: {intent.arg or 'the product'}",
        "insights": intent.arg or "Give me the latest insights.",
        "fix": f"The brand's site has a bug: {intent.arg or 'broken output'}. Use fix_site to diagnose and repair it in the sandbox, then report before/after.",
        "edit": f"Use edit_product_image to: {intent.arg or 'improve the product image'}.",
        "video": "Use start_video_session to open a live video + screen-share room and give me the join link.",
    }.get(intent.action, intent.arg)

    try:
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post(f"{AGENT_BASE_URL}/chat", headers=_headers(),
                             json={"message": directive, "participant": "asi-one"})
            r.raise_for_status()
            return _last_message_from_sse(r.text)
    except Exception as exc:  # noqa: BLE001
        return f"(control plane unreachable: {exc})"


async def _get_health() -> str:
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"{AGENT_BASE_URL}/health")
            data = r.json()
        return (f"TwoCustomer online. LLM={data.get('llm')}, "
                f"tools={', '.join(data.get('tools', []))}.")
    except Exception as exc:  # noqa: BLE001
        return f"(status unavailable: {exc})"


def _last_message_from_sse(body: str) -> str:
    """Pull the final `message` event text out of an SSE response body."""
    text = ""
    for block in body.split("\n\n"):
        event = "message"
        data = ""
        for line in block.splitlines():
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                data += line[5:].strip()
        if event in ("message", "error") and data:
            try:
                obj = json.loads(data)
                text = obj.get("text") or obj.get("error") or text
            except json.JSONDecodeError:
                pass
    return text or "Done."
