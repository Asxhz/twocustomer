"""Trivial echo tool — proves registry + dispatch wiring in P1 tests."""

from __future__ import annotations

from .registry import registry


@registry.tool(
    name="echo",
    description="Echo a message back. Used to verify tool wiring.",
    input_schema={
        "type": "object",
        "properties": {"message": {"type": "string"}},
        "required": ["message"],
    },
)
async def echo(message: str) -> str:
    return f"echo: {message}"
