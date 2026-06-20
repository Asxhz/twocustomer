"""Token/cost estimation + context trimming.

Heuristic (no network): ~4 chars/token. Trimming keeps the most recent turns
under a budget so long conversations don't blow the context window. Pricing
reflects claude-sonnet-4-6 ($3/MTok in, $15/MTok out).
"""

from __future__ import annotations

from typing import Any

_CHARS_PER_TOKEN = 4
_IN_PER_MTOK = 3.0
_OUT_PER_MTOK = 15.0


def estimate_tokens(text: str) -> int:
    return max(1, len(text or "") // _CHARS_PER_TOKEN)


def _content_len(content: Any) -> int:
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        total = 0
        for block in content:
            if isinstance(block, dict):
                total += len(str(block.get("text", "")) + str(block.get("content", "")))
            else:
                total += len(str(block))
        return total
    return len(str(content))


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """USD cost estimate for claude-sonnet-4-6."""
    return round(
        input_tokens / 1_000_000 * _IN_PER_MTOK
        + output_tokens / 1_000_000 * _OUT_PER_MTOK,
        6,
    )


def trim_messages(
    messages: list[dict[str, Any]], *, max_chars: int = 200_000
) -> list[dict[str, Any]]:
    """Keep the most recent messages whose combined size is under max_chars.

    Always preserves order; never splits a message. Returns a new list.
    """
    kept: list[dict[str, Any]] = []
    used = 0
    for m in reversed(messages):
        size = _content_len(m.get("content"))
        if used + size > max_chars and kept:
            break
        kept.append(m)
        used += size
    kept.reverse()
    return kept
