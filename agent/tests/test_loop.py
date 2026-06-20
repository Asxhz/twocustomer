"""P1.18 — agent loop runs a tool round-trip with the stub LLM."""

import pytest

from app.core.loop import run_agent
from app.llm.stub import StubLLM
from app.tools import echo  # noqa: F401 - registers echo
from app.tools.registry import registry


@pytest.mark.asyncio
async def test_loop_plain_reply():
    msgs = [{"role": "user", "content": "hello"}]
    res = await run_agent(llm=StubLLM(), registry=registry,
                          system="sys", messages=msgs)
    assert res.text.startswith("stub reply:")
    assert res.rounds == 1
    assert res.tool_log == []


@pytest.mark.asyncio
async def test_loop_tool_round_trip():
    msgs = [{"role": "user", "content": "please use echo on this"}]
    res = await run_agent(llm=StubLLM(), registry=registry,
                          system="sys", messages=msgs)
    # stub: round 1 -> echo tool, round 2 -> final "done: echo: ..."
    assert res.rounds == 2
    assert len(res.tool_log) == 1
    assert res.tool_log[0]["name"] == "echo"
    assert "echo:" in res.tool_log[0]["output"]
    assert res.text.startswith("done:")
