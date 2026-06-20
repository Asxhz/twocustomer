"""recall_memory tool — lets the agent pull relevant past insights into context.

Demonstrates Redis "beyond caching": the agent answers a new question by citing
prior findings retrieved from memory.
"""

from __future__ import annotations

from app.state.memory import recall

from .registry import registry


@registry.tool(
    name="recall_memory",
    description=(
        "Recall relevant past insights/campaigns for a brand from memory before "
        "answering. Use when the user references earlier findings or asks what "
        "you've learned."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "brand": {"type": "string", "description": "Brand slug or name."},
            "query": {"type": "string", "description": "What to recall about."},
        },
        "required": ["brand", "query"],
    },
)
async def recall_memory(brand: str, query: str) -> str:
    items = await recall(brand, query, k=3)
    if not items:
        return "No relevant prior memory."
    return "\n".join(f"- ({it.kind}) {it.text}" for it in items)
