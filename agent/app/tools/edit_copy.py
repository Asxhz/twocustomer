"""Rewrite product copy / format with Claude (on-brand, to a target style)."""

from __future__ import annotations

from app.config import get_settings

from .registry import registry


@registry.tool(
    name="edit_copy",
    description=(
        "Rewrite product copy, a description, or any text to a target style "
        "(shorter, cleaner, more premium, friendlier, different format). Use for "
        "'make this lighter/punchier/on-brand'."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "The copy to rewrite."},
            "instruction": {"type": "string",
                            "description": "How to change it (style/length/format)."},
        },
        "required": ["text", "instruction"],
    },
)
async def edit_copy(text: str, instruction: str) -> str:
    s = get_settings()
    if not s.has_anthropic():
        return "Copy editing needs ANTHROPIC_API_KEY."
    from app.llm.claude import ClaudeLLM

    llm = ClaudeLLM(max_tokens=500)
    resp = await llm.complete(
        system=("You are a brand copywriter. Rewrite the given copy per the "
                "instruction. Keep it accurate to the product. Return ONLY the "
                "rewritten copy, no preamble."),
        messages=[{"role": "user",
                   "content": f"INSTRUCTION: {instruction}\n\nCOPY:\n{text}"}],
    )
    return resp.text.strip()
