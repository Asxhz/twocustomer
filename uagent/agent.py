"""TwoCustomer uAgent — discoverable on ASI:One via the Chat Protocol.

A user finds TwoCustomer through ASI:One, sends natural language, and the agent
parses intent and takes real action by driving the TwoCustomer control plane
(monitor a brand, build a campaign, run a customer interview, fetch insights) —
more than a chatbot or an API wrapper.

Run:  uv run python agent.py     (needs UAGENT_SEED + a funded AGENT_BASE_URL)
Publishes its manifest so it shows up in Agentverse / ASI:One search.

Best Use of Fetch AI track (UC Berkeley AI Hackathon).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# Load the repo-root .env so UAGENT_SEED / AGENT_BASE_URL / AGENTVERSE_API_KEY are
# picked up without manual `export`. Must run before control_plane is imported.
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

from control_plane import handle
from intent import parse_intent

SEED = os.environ.get("UAGENT_SEED", "twocustomer-dev-seed-change-me")

agent = Agent(
    name="twocustomer",
    seed=SEED,  # loaded from .env (UAGENT_SEED) — derives the stable address
    port=int(os.environ.get("UAGENT_PORT", "8001")),
    mailbox=True,  # route through Agentverse so ASI:One can reach it
    description=(
        "The AI forward-deployed agent team for consumer brands. Ask it to "
        "monitor a brand, build a campaign, interview customers, or surface "
        "insights — it takes real action through the TwoCustomer engine."
    ),
    publish_agent_details=True,  # auto-publish profile to your Agentverse account
)

chat = Protocol(spec=chat_protocol_spec)


def _text(msg: ChatMessage) -> str:
    return " ".join(c.text for c in msg.content if isinstance(c, TextContent)).strip()


@chat.on_message(ChatMessage)
async def on_chat(ctx: Context, sender: str, msg: ChatMessage) -> None:
    # 1) acknowledge receipt (chat-protocol requirement)
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id
        ),
    )
    # 2) parse intent → take action via the control plane
    text = _text(msg)
    ctx.logger.info(f"asi:one message: {text!r}")
    intent = parse_intent(text)
    reply = await handle(intent)
    # 3) reply
    await ctx.send(
        sender,
        ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=reply)],
        ),
    )


@chat.on_message(ChatAcknowledgement)
async def on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement) -> None:
    ctx.logger.debug(f"ack from {sender}")


agent.include(chat, publish_manifest=True)


if __name__ == "__main__":
    print(f"TwoCustomer uAgent address: {agent.address}")
    agent.run()
