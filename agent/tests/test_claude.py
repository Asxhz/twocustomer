"""P2.06/P2.16 — Claude live tests. Skipped when ANTHROPIC_API_KEY is unset."""

import os

import pytest

from app.core.loop import run_agent
from app.tools import echo  # noqa: F401 - registers echo
from app.tools.registry import registry

requires_key = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)


def _skip_if_billing(exc: Exception) -> None:
    """Account-level billing/credit errors aren't code failures — skip, don't fail."""
    msg = str(exc)
    if "credit balance" in msg or "Billing" in msg or "billing" in msg:
        pytest.skip(f"Anthropic account not funded: {msg[:80]}")
    raise exc


@requires_key
@pytest.mark.live
@pytest.mark.asyncio
async def test_claude_completion():
    from app.llm.claude import ClaudeLLM

    llm = ClaudeLLM()
    try:
        res = await llm.complete(
            system="You are terse. Reply with one word.",
            messages=[{"role": "user", "content": "Say hello in one word."}],
        )
    except Exception as exc:  # noqa: BLE001
        _skip_if_billing(exc)
    assert res.text  # non-empty reply


@requires_key
@pytest.mark.live
@pytest.mark.asyncio
async def test_claude_tool_round_trip():
    from app.llm.claude import ClaudeLLM

    msgs = [{"role": "user",
             "content": "Call the echo tool with message 'ping', then tell me what it returned."}]
    try:
        res = await run_agent(llm=ClaudeLLM(), registry=registry,
                              system="Use tools when asked.", messages=msgs)
    except Exception as exc:  # noqa: BLE001
        _skip_if_billing(exc)
    assert any(t["name"] == "echo" for t in res.tool_log)
    assert res.text
