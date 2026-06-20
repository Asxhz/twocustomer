"""V6 Daily video — tool registered + graceful degrade without key."""

import pytest
from fastapi.testclient import TestClient

from app.channels import daily
from app.main import app
from app.tools import video_tool  # noqa: F401 - registers start_video_session
from app.tools.registry import registry

client = TestClient(app)


def test_tool_registered():
    assert "start_video_session" in registry.names()


@pytest.mark.asyncio
async def test_degrades_without_key():
    if daily.is_configured():
        pytest.skip("DAILY_API_KEY set")
    out = await video_tool.start_video_session("Rosie")
    assert "DAILY_API_KEY not set" in out


def test_session_video_endpoint_degrades():
    r = client.post("/session/video")
    assert r.status_code == 200
    body = r.json()
    # without a key it degrades cleanly; with a key it returns a room_url
    assert "room_url" in body
