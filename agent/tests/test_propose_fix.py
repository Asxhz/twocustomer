"""P2.26/P2.27/P2.29 — propose_fix produces a structured, persisted packet."""

import pytest

from app.tools import propose_fix as pf
from app.tools.registry import registry


def test_registered():
    assert "propose_fix" in registry.names()


@pytest.mark.asyncio
async def test_packet_structure():
    out = await pf.propose_fix(
        brand="aurora",
        signal="Stockouts at 3 retail accounts are costing ~10% of revenue.",
        evidence=["@thirsty_sam: sold out again", "BevReview: yuzu breakout"],
    )
    assert "Packet ready" in out and "Artifact" in out
    packet = pf.LAST_PACKET["aurora"]
    for key in ("title", "summary", "evidence", "recommendedAction", "artifact"):
        assert key in packet and packet[key]
    assert len(packet["evidence"]) == 2
    assert packet["title"].startswith("Stockouts")


@pytest.mark.asyncio
async def test_dispatch_via_registry():
    out = await registry.dispatch(
        "propose_fix", {"brand": "x", "signal": "Email flow dropped CTR 34%."}
    )
    assert "Packet ready" in out
