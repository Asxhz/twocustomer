"""Per-task model routing. Efficient by default: Haiku for most work, Sonnet for
quality-sensitive tasks, Opus only rarely (complex planning/orchestration).

Override any tier via env (ANTHROPIC_MODEL_HAIKU / _SONNET / _OPUS).
"""

from __future__ import annotations

import os

HAIKU = os.environ.get("ANTHROPIC_MODEL_HAIKU", "claude-haiku-4-5-20251001")
SONNET = os.environ.get("ANTHROPIC_MODEL_SONNET", "claude-sonnet-4-6")
OPUS = os.environ.get("ANTHROPIC_MODEL_OPUS", "claude-opus-4-8")

# Quality-sensitive tasks get Sonnet. Everything else (chat, classify, score,
# monitor, routing, validate) stays on Haiku for speed + cost.
_SONNET_TASKS = {
    "fde_diagnose", "campaign", "copy", "interview_synth", "analyst", "fixer", "research_synth",
}
# Reserved for rare, genuinely complex multi-step planning.
_OPUS_TASKS = {"planner"}


def model_for(task: str) -> str:
    if task in _OPUS_TASKS:
        return OPUS
    if task in _SONNET_TASKS:
        return SONNET
    return HAIKU
