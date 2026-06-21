"""Tool registry. Tools declare a name, JSON-schema input, and an async run().

The Claude client (P2) converts registered tools to the Anthropic tool format;
the loop dispatches tool_use blocks here. External SDK calls live inside each
tool's run() so the registry stays dependency-free and unit-testable.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

ToolFn = Callable[..., Awaitable[Any]]


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]  # JSON schema (Anthropic `input_schema` shape)
    run: ToolFn


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def tool(
        self, name: str, description: str, input_schema: dict[str, Any]
    ) -> Callable[[ToolFn], ToolFn]:
        """Decorator form."""

        def deco(fn: ToolFn) -> ToolFn:
            self.register(Tool(name=name, description=description,
                               input_schema=input_schema, run=fn))
            return fn

        return deco

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"unknown tool: {name}")
        return self._tools[name]

    def names(self) -> list[str]:
        return sorted(self._tools)

    def without(self, exclude: set[str]) -> "ToolRegistry":
        """A view of this registry with some tools removed (role gating).

        Shares the underlying Tool objects; only the visible set differs, so the
        model is never offered (and can never dispatch) an excluded tool.
        """
        sub = ToolRegistry()
        sub._tools = {n: t for n, t in self._tools.items() if n not in exclude}
        return sub

    def specs(self) -> list[dict[str, Any]]:
        """Anthropic-format tool specs."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
            }
            for t in self._tools.values()
        ]

    async def dispatch(self, name: str, args: dict[str, Any], **ctx: Any) -> str:
        """Run a tool by name. Returns a string (tool_result content).

        Tool failures are caught and returned as an error string so the model
        can recover instead of the loop crashing.
        """
        try:
            tool = self.get(name)
        except KeyError as exc:
            return f"ERROR: {exc}"
        try:
            # pass only ctx kwargs the tool actually accepts
            sig = inspect.signature(tool.run)
            accepted = {k: v for k, v in ctx.items() if k in sig.parameters}
            result = await tool.run(**args, **accepted)
            return result if isinstance(result, str) else _to_str(result)
        except Exception as exc:  # noqa: BLE001 - surface to model, never crash loop
            return f"ERROR running {name}: {exc}"


def _to_str(value: Any) -> str:
    import json

    try:
        return json.dumps(value, default=str)
    except Exception:
        return str(value)


# Process-wide default registry.
registry = ToolRegistry()
