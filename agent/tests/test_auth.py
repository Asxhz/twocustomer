"""Agent shared-token guard — enforces when AGENT_SHARED_TOKEN is configured."""

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

client = TestClient(app)


def test_token_guard_rejects_without_token(monkeypatch):
    monkeypatch.setattr(get_settings(), "shared_token", "s3cret", raising=False)
    # protected endpoint, no Authorization header
    r = client.post("/monitor/config", json={"brand_slug": "x", "terms": ["x"]})
    assert r.status_code == 401


def test_token_guard_allows_with_token(monkeypatch):
    monkeypatch.setattr(get_settings(), "shared_token", "s3cret", raising=False)
    r = client.post("/monitor/config", json={"brand_slug": "x", "terms": ["x"]},
                    headers={"Authorization": "Bearer s3cret"})
    assert r.status_code == 200


def test_health_open_even_with_token(monkeypatch):
    monkeypatch.setattr(get_settings(), "shared_token", "s3cret", raising=False)
    assert client.get("/health").status_code == 200  # health is not protected
