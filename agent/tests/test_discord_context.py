"""Discord read-context helper + endpoint (offline)."""

import httpx
import pytest
import respx

from app.channels import discord
from app.config import get_settings


@pytest.mark.asyncio
async def test_read_context_empty_without_config(monkeypatch):
    monkeypatch.setattr(get_settings(), "discord_bot_token", "", raising=False)
    monkeypatch.setattr(get_settings(), "discord_channel_id", "", raising=False)
    assert await discord.read_context() == ""


@pytest.mark.asyncio
@respx.mock
async def test_read_context_formats_messages(monkeypatch):
    monkeypatch.setattr(get_settings(), "discord_bot_token", "botkey", raising=False)
    monkeypatch.setattr(get_settings(), "discord_channel_id", "123", raising=False)
    respx.get("https://discord.com/api/v10/channels/123/messages").mock(
        return_value=httpx.Response(200, json=[
            {"author": {"username": "founder"}, "content": "CTA button is broken"},
            {"author": {"username": "support"}, "content": ""},  # skipped (no text)
            {"author": {"username": "team"}, "content": "hero copy is placeholder"},
        ]))
    out = await discord.read_context()
    # newest-first from the API -> rendered oldest-first
    assert out == "team: hero copy is placeholder\nfounder: CTA button is broken"
