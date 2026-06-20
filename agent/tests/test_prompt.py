"""P2.09 — system prompt loads and carries the TwoCustomer persona."""

from app.main import SYSTEM_PROMPT


def test_prompt_loaded():
    assert SYSTEM_PROMPT and len(SYSTEM_PROMPT) > 200


def test_prompt_persona():
    p = SYSTEM_PROMPT.lower()
    assert "twocustomer" in p
    for kw in ("monitor", "insight", "act"):
        assert kw in p
