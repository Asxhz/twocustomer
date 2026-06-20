"""Intent-routing eval fixtures: prompt → the tool we expect the agent to call.

`stub_safe=True` cases are deterministically routable by StubLLM (offline CI).
The rest exercise real intent routing and run only against Claude (funded).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EvalCase:
    prompt: str
    expect_tool: str
    stub_safe: bool = False


CASES: list[EvalCase] = [
    EvalCase("please use echo on the word ping", "echo", stub_safe=True),
    EvalCase("monitor Aurora Drinks for me", "monitor_brand"),
    EvalCase("what are people saying about Aurora right now?", "monitor_brand"),
    EvalCase("recall what we found about stockouts", "recall_memory"),
    EvalCase("turn the stockout finding into a packet we can ship", "propose_fix"),
]
