"""Handler robustness — voice degrades cleanly; default scrapers present."""

import pytest
from fastapi.testclient import TestClient

from app.channels import deepgram
from app.main import app
from app.monitor.scrapers import DEFAULT_SCRAPERS, hn_search

client = TestClient(app)

# These assert the unconfigured (no key) degrade path. When DEEPGRAM_API_KEY is
# set (real demo env), voice actually works, so skip.
no_deepgram = pytest.mark.skipif(
    deepgram.is_configured(), reason="DEEPGRAM_API_KEY set — voice is live, not degraded"
)


@no_deepgram
def test_voice_transcribe_degrades_503():
    r = client.post("/voice/transcribe", content=b"x",
                    headers={"Content-Type": "audio/wav"})
    assert r.status_code == 503
    assert "DEEPGRAM" in r.json()["error"]


@no_deepgram
def test_voice_speak_degrades_503():
    r = client.post("/voice/speak", json={"message": "hello"})
    assert r.status_code == 503


def test_default_scrapers_include_hn():
    assert hn_search in DEFAULT_SCRAPERS
    assert len(DEFAULT_SCRAPERS) >= 2


def test_health_lists_all_tools():
    tools = client.get("/health").json()["tools"]
    for t in ("monitor_brand", "propose_fix", "create_campaign", "recall_memory"):
        assert t in tools
