"""Deterministic stub LLM for tests + offline dev.

Scripted behavior: if the latest user message contains "use echo", it emits one
echo tool call on the first turn, then returns final text after seeing the tool
result. Otherwise it echoes the last user text. No network, no key.
"""

from __future__ import annotations

from typing import Any, AsyncIterator

from .base import LLMClient, LLMResponse, StreamEvent, ToolCall


class StubLLM(LLMClient):
    def __init__(self) -> None:
        self._calls = 0

    async def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        self._calls += 1
        last_user = _last_user_text(messages)

        # If a tool_result is already present, wrap up.
        if _has_tool_result(messages):
            return LLMResponse(text="done: " + _last_tool_output(messages))

        if tools and "use echo" in last_user.lower():
            return LLMResponse(
                tool_calls=[ToolCall(id="t1", name="echo",
                                     input={"message": last_user})],
                stop_reason="tool_use",
            )
        return LLMResponse(text=f"stub reply: {last_user}")

    async def stream(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamEvent]:
        resp = await self.complete(system=system, messages=messages, tools=tools)
        for tok in resp.text.split(" "):
            yield StreamEvent(type="token", data={"text": tok + " "})
        yield StreamEvent(type="done", data={"text": resp.text})


def _last_user_text(messages: list[dict[str, Any]]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            c = m.get("content")
            if isinstance(c, str):
                return c
            if isinstance(c, list):
                for block in c:
                    if isinstance(block, dict) and block.get("type") == "text":
                        return block.get("text", "")
    return ""


def _has_tool_result(messages: list[dict[str, Any]]) -> bool:
    for m in messages:
        c = m.get("content")
        if isinstance(c, list):
            for block in c:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    return True
    return False


def _last_tool_output(messages: list[dict[str, Any]]) -> str:
    for m in reversed(messages):
        c = m.get("content")
        if isinstance(c, list):
            for block in c:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    return str(block.get("content", ""))
    return ""
