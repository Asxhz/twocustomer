"""P3.30/P3.31/P3.32 — monitor config model + CRUD roundtrip."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.monitor.config import MonitorConfig, get_config, save_config

client = TestClient(app)


def test_model_validates_bounds():
    cfg = MonitorConfig(brand_slug="aurora", terms=["Aurora"], interval_minutes=15,
                        threshold=0.8)
    assert cfg.interval_minutes == 15
    with pytest.raises(Exception):
        MonitorConfig(brand_slug="x", threshold=2.0)  # > 1.0


@pytest.mark.asyncio
async def test_store_roundtrip():
    await save_config(MonitorConfig(brand_slug="brandY", terms=["y"]))
    got = await get_config("brandY")
    assert got is not None and got.terms == ["y"]


def test_crud_endpoints():
    r = client.post("/monitor/config", json={
        "brand_slug": "aurora-drinks", "terms": ["Aurora Drinks", "@auroradrinks"],
        "interval_minutes": 20, "threshold": 0.75,
    })
    assert r.status_code == 200
    assert r.json()["config"]["interval_minutes"] == 20

    g = client.get("/monitor/config/aurora-drinks")
    assert g.status_code == 200
    assert g.json()["config"]["terms"] == ["Aurora Drinks", "@auroradrinks"]


def test_get_unknown_returns_null():
    r = client.get("/monitor/config/never-configured")
    assert r.status_code == 200 and r.json()["config"] is None
