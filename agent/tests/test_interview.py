"""P4.29-4.34 — interview FSM transitions + transcript -> insight."""

import pytest

from app.interview.fsm import DEFAULT_QUESTIONS, Interview
from app.interview.synth import synth_session


def test_fsm_flow():
    iv = Interview(brand="aurora", customer="Rosie")
    q0 = iv.start()
    assert q0 == DEFAULT_QUESTIONS[0]
    assert iv.progress() == (0, len(DEFAULT_QUESTIONS))

    nxt = iv.answer("better flavor")
    assert nxt == DEFAULT_QUESTIONS[1]
    assert not iv.done

    # answer the rest
    for _ in range(len(DEFAULT_QUESTIONS) - 1):
        iv.answer("ok")
    assert iv.done
    assert iv.answer("late") is None  # no-op after done
    assert len(iv.customer_answers()) == len(DEFAULT_QUESTIONS)


@pytest.mark.asyncio
async def test_synth_session_heuristic():
    iv = Interview(brand="aurora", customer="Rosie")
    iv.start()
    iv.answer("short")
    iv.answer("I almost cancelled because pausing my subscription was impossible to find")
    iv.answer("yes")
    iv.answer("maybe")
    insight = await synth_session(iv, channel="voice")
    assert insight["title"].startswith("Interview")
    assert "pausing" in insight["body"].lower()  # longest answer becomes the lead
