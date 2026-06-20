"""P2.33/P2.36/P2.37 — token/cost estimate + context trim."""

from app.llm.budget import estimate_cost, estimate_tokens, trim_messages


def test_estimate_tokens():
    assert estimate_tokens("") == 1
    assert estimate_tokens("a" * 40) == 10


def test_estimate_cost_monotonic():
    cheap = estimate_cost(1000, 100)
    pricey = estimate_cost(100000, 50000)
    assert pricey > cheap > 0
    # claude-sonnet-4-6 pricing: $3/MTok in, $15/MTok out (output 5x input)
    assert estimate_cost(0, 1_000_000) == 15.0
    assert estimate_cost(1_000_000, 0) == 3.0


def test_trim_keeps_recent_under_budget():
    msgs = [{"role": "user", "content": "x" * 100} for _ in range(10)]
    trimmed = trim_messages(msgs, max_chars=250)
    assert len(trimmed) == 2  # 2*100=200 <= 250, 3rd would exceed
    assert trimmed == msgs[-2:]


def test_trim_never_empty():
    msgs = [{"role": "user", "content": "x" * 1000}]
    # even if one message exceeds budget, keep at least the latest
    assert trim_messages(msgs, max_chars=10) == msgs


def test_trim_handles_block_content():
    msgs = [
        {"role": "assistant",
         "content": [{"type": "text", "text": "hi"},
                     {"type": "tool_use", "input": {}}]},
        {"role": "user", "content": "ok"},
    ]
    assert len(trim_messages(msgs, max_chars=100)) == 2
