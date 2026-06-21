"""Tool registry. Tools declare a name, JSON-schema input, and an async run().

The Claude client (P2) converts registered tools to the Anthropic tool format;
the loop dispatches tool_use blocks here. External SDK calls live inside each
tool's run() so the registry stays dependency-free and unit-testable.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

ToolFn = Callable[..., Awaitable[Any]]

logger = logging.getLogger("twocustomer.tools")

# A single tool call may not block the agent turn forever (a dead upstream, a
# slow deploy). FDE tools that build + deploy need a generous ceiling.
_TOOL_TIMEOUT_S = 240
_MAX_OUTPUT = 100_000


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
        # Validate required args up front so a missing field is a clear message
        # the model can recover from, not a confusing TypeError.
        required = (tool.input_schema or {}).get("required", []) or []
        missing = [k for k in required if k not in (args or {})]
        if missing:
            return f"ERROR: {name} needs {', '.join(missing)}. Provide it and retry."
        try:
            # pass only ctx kwargs the tool actually accepts
            sig = inspect.signature(tool.run)
            accepted = {k: v for k, v in ctx.items() if k in sig.parameters}
            result = await asyncio.wait_for(
                tool.run(**args, **accepted), timeout=_TOOL_TIMEOUT_S)
            return result if isinstance(result, str) else _to_str(result)
        except asyncio.TimeoutError:
            logger.warning("tool %s timed out after %ss", name, _TOOL_TIMEOUT_S)
            return (f"ERROR running {name}: it took too long. Tell the user it is still "
                    "working and to try again in a moment.")
        except Exception as exc:  # noqa: BLE001 - surface to model, never crash loop
            logger.exception("tool %s failed", name)
            return f"ERROR running {name}: {str(exc)[:200]}"


def _to_str(value: Any) -> str:
    import json

    try:
        out = json.dumps(value, default=str)
    except Exception:  # noqa: BLE001
        out = str(value)
    return out if len(out) <= _MAX_OUTPUT else out[:_MAX_OUTPUT] + "...(truncated)"


# Process-wide default registry.
registry = ToolRegistry()
