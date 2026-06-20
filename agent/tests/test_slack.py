"""P4.06/P4.08 — Slack signature verify (pure) + url_verification handshake."""

import hashlib
import hmac
import time

from fastapi.testclient import TestClient

from app.channels import slack
from app.main import app

client = TestClient(app)
SECRET = "test-signing-secret"


def _sign(ts: str, body: str) -> str:
    base = f"v0:{ts}:{body}".encode()
    digest = hmac.new(SECRET.encode(), base, hashlib.sha256).hexdigest()
    return f"v0={digest}"


def test_verify_good_signature():
    ts = str(int(time.time()))
    body = '{"type":"event_callback"}'
    sig = _sign(ts, body)
    assert slack.verify_signature(signing_secret=SECRET, timestamp=ts,
                                  body=body, signature=sig)


def test_verify_bad_signature():
    ts = str(int(time.time()))
    assert not slack.verify_signature(signing_secret=SECRET, timestamp=ts,
                                      body="x", signature="v0=deadbeef")


def test_verify_rejects_stale_timestamp():
    old = str(int(time.time()) - 9999)
    body = "{}"
    assert not slack.verify_signature(signing_secret=SECRET, timestamp=old,
                                      body=body, signature=_sign(old, body))


def test_url_verification_challenge():
    r = client.post("/slack/events", json={"type": "url_verification",
                                           "challenge": "abc123"})
    assert r.status_code == 200
    assert r.json()["challenge"] == "abc123"


def test_insight_blocks_shape():
    blocks = slack.insight_blocks("Stockout leak", "10% of revenue", "risk")
    assert blocks[0]["type"] == "header"
    assert "🔴" in blocks[0]["text"]["text"]
