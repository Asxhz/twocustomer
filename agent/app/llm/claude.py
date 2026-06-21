"""Anthropic Claude implementation of the LLMClient protocol.

Model: claude-sonnet-4-6 (configurable via ANTHROPIC_MODEL). Follows the 2026 API
surface — no temperature/budget_tokens; effort=medium for balance.
Parses tool_use blocks into ToolCall; the loop returns tool_result blocks.
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from anthropic import AsyncAnthropic

from app.config import get_settings

from .base import LLMClient, LLMResponse, StreamEvent, ToolCall
from .retry import retry_async

logger = logging.getLogger("twocustomer.claude")


class ClaudeLLM(LLMClient):
    def __init__(self, *, max_tokens: int = 4096, model: str | None = None) -> None:
        s = get_settings()
        if not s.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        self._client = AsyncAnthropic(api_key=s.anthropic_api_key)
        # Per-task model routing; falls back to the configured default.
        self._model = model or s.anthropic_model
        self._max_tokens = max_tokens

    def _kwargs(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            # System as a cacheable block (prefix caching). Caches only once the
            # prefix clears the model minimum (~4096 tok on opus); harmless below.
            "system": [{"type": "text", "text": system,
                        "cache_control": {"type": "ephemeral"}}],
            "messages": messages,
        }
        # The effort/output_config knob is only supported by some models (not
        # Haiku) — sending it to Haiku 400s. Include it only where supported.
        if "haiku" not in self._model.lower():
            kwargs["output_config"] = {"effort": "medium"}
        if tools:
            kwargs["tools"] = tools
        return kwargs

    async def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        kwargs = self._kwargs(system=system, messages=messages, tools=tools)
        resp = await retry_async(lambda: self._client.messages.create(**kwargs))
        if resp.stop_reason == "refusal":
            return LLMResponse(text="(declined)", stop_reason="refusal")

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(id=block.id, name=block.name,
                             input=dict(block.input or {}))
                )
        return LLMResponse(
            text="".join(text_parts).strip(),
            tool_calls=tool_calls,
            stop_reason=resp.stop_reason or "end_turn",
        )

    async def stream(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamEvent]:
        """Token stream. Tool-use turns are surfaced as a single tool event then
        handled by the loop; final text streams token-by-token."""
        async with self._client.messages.stream(
            **self._kwargs(system=system, messages=messages, tools=tools)
        ) as stream:
            async for text in stream.text_stream:
                yield StreamEvent(type="token", data={"text": text})
            final = await stream.get_final_message()
        yield StreamEvent(type="done", data={"stop_reason": final.stop_reason})
