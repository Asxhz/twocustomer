"""Provider-agnostic agent loop.

Drives: model -> (tool calls)* -> final text. The LLM client is injected so the
loop is unit-testable with a stub (P1) and runs on Claude in P2. Tool execution
goes through the ToolRegistry; results are fed back as user/tool messages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.llm.base import LLMClient
from app.llm.budget import trim_messages
from app.tools.registry import ToolRegistry

MAX_TOOL_ROUNDS = 6


@dataclass
class AgentResult:
    text: str
    rounds: int
    tool_log: list[dict[str, Any]]


async def run_agent(
    *,
    llm: LLMClient,
    registry: ToolRegistry,
    system: str,
    messages: list[dict[str, Any]],
    context: dict[str, Any] | None = None,
    max_rounds: int = MAX_TOOL_ROUNDS,
) -> AgentResult:
    """Run the tool-calling loop until the model returns final text.

    `messages` is the running conversation in Anthropic shape
    ([{role, content}]). It is mutated in place with assistant/tool turns so the
    caller can persist the full transcript.
    """
    ctx = context or {}
    tool_specs = registry.specs()
    tool_log: list[dict[str, Any]] = []

    for round_i in range(1, max_rounds + 1):
        # Cap context so long tool loops never blow the window.
        sent = trim_messages(messages, max_chars=600_000)
        resp = await llm.complete(system=system, messages=sent, tools=tool_specs)

        if not resp.wants_tools:
            messages.append({"role": "assistant", "content": resp.text})
            return AgentResult(text=resp.text, rounds=round_i, tool_log=tool_log)

        # Record the assistant turn that requested the tools (Anthropic shape).
        assistant_content: list[dict[str, Any]] = []
        if resp.text:
            assistant_content.append({"type": "text", "text": resp.text})
        for call in resp.tool_calls:
            assistant_content.append(
                {"type": "tool_use", "id": call.id, "name": call.name,
                 "input": call.input}
            )
        messages.append({"role": "assistant", "content": assistant_content})

        # Execute tools, append a single user turn with all tool_results.
        results_content: list[dict[str, Any]] = []
        for call in resp.tool_calls:
            output = await registry.dispatch(call.name, call.input, **ctx)
            tool_log.append({"name": call.name, "input": call.input, "output": output})
            results_content.append(
                {"type": "tool_result", "tool_use_id": call.id, "content": output}
            )
        messages.append({"role": "user", "content": results_content})

    # Hit round cap — force a final plain answer with tools disabled.
    resp = await llm.complete(system=system, messages=messages, tools=None)
    messages.append({"role": "assistant", "content": resp.text})
    return AgentResult(text=resp.text, rounds=max_rounds, tool_log=tool_log)
