"""P2.40-2.43 — intent-routing eval harness.

Offline: the stub-safe subset must pass against StubLLM. Funded: the full set
runs against Claude (skipped without credits)."""

import os

import pytest

from app.eval.fixtures import CASES
from app.eval.runner import run_eval
from app.llm.stub import StubLLM


def test_fixtures_present():
    assert len(CASES) >= 5
    assert any(c.stub_safe for c in CASES)
    assert all(c.expect_tool for c in CASES)


@pytest.mark.asyncio
async def test_stub_routing_passes():
    outcomes = await run_eval(StubLLM(), stub_only=True)
    assert outcomes
    assert all(o.passed for o in outcomes)  # echo case routes correctly


@pytest.mark.live
@pytest.mark.skipif(not os.environ.get("RUN_CLAUDE_EVAL"),
                    reason="set RUN_CLAUDE_EVAL=1 to run the full Claude eval")
@pytest.mark.asyncio
async def test_full_claude_eval():
    from app.llm.claude import ClaudeLLM

    outcomes = await run_eval(ClaudeLLM())
    passed = sum(o.passed for o in outcomes)
    assert passed >= len(outcomes) - 1  # allow one miss
