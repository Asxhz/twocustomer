"""P1.14 — health endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "echo" in body["tools"]


def test_health_reports_llm_mode():
    r = client.get("/health")
    assert r.json()["llm"] in {"claude", "stub"}
