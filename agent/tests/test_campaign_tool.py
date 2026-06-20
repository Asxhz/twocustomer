"""create_campaign drafts a structured campaign + registers."""

import pytest

from app.tools import campaign_tool as ct
from app.tools.registry import registry


def test_registered():
    assert "create_campaign" in registry.names()


@pytest.mark.asyncio
async def test_draft_structure():
    out = await ct.create_campaign("aurora", "promote the yuzu sparkling SKU")
    assert "Campaign ready" in out
    c = ct.LAST_CAMPAIGN["aurora"]
    assert c["status"] == "ready"
    for section in ("## Concept", "## Hooks", "## Channels", "## Success metrics"):
        assert section in c["body"]


@pytest.mark.asyncio
async def test_dispatch():
    out = await registry.dispatch(
        "create_campaign", {"brand": "x", "brief": "summer refresh"}
    )
    assert "Campaign ready" in out
