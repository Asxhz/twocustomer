"""Provider-agnostic LLM interface.

The agent loop depends only on this protocol; the Claude client (P2) implements
it, and tests inject a stub. Keeps the loop testable without an API key.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Protocol, runtime_checkable


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class LLMResponse:
    """One model turn. Either final text, or one+ tool calls to execute."""

    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"

    @property
    def wants_tools(self) -> bool:
        return bool(self.tool_calls)


@dataclass
class StreamEvent:
    """Streamed agent event surfaced to channels (SSE)."""

    type: str  # token | tool_start | tool_end | artifact | done | error
    data: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class LLMClient(Protocol):
    """Minimal contract the agent loop needs."""

    async def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """One non-streaming turn. Returns text and/or tool calls."""
        ...

    def stream(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamEvent]:
        """Stream a turn as StreamEvents. Default impl can wrap complete()."""
        ...
