"""Run the intent-routing eval: for each case, run one agent turn and check
whether the expected tool fired.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.loop import run_agent
from app.llm.base import LLMClient
from app.tools import echo, memory_tool, monitor_tool, propose_fix  # noqa: F401
from app.tools.registry import registry

from .fixtures import CASES, EvalCase


@dataclass
class EvalOutcome:
    case: EvalCase
    fired: list[str]
    passed: bool


async def run_case(llm: LLMClient, case: EvalCase) -> EvalOutcome:
    res = await run_agent(
        llm=llm, registry=registry, system="Route to the right tool.",
        messages=[{"role": "user", "content": case.prompt}], max_rounds=2,
    )
    fired = [e["name"] for e in res.tool_log]
    return EvalOutcome(case=case, fired=fired, passed=case.expect_tool in fired)


async def run_eval(llm: LLMClient, *, stub_only: bool = False) -> list[EvalOutcome]:
    cases = [c for c in CASES if c.stub_safe] if stub_only else CASES
    return [await run_case(llm, c) for c in cases]
