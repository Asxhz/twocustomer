"""Discord channel — Ed25519 verify + PING->PONG + command extraction."""

import json

from app.channels import discord


def _keypair():
    from nacl.signing import SigningKey

    sk = SigningKey.generate()
    pub = sk.verify_key.encode().hex()
    return sk, pub


def test_verify_good_and_bad_signature():
    sk, pub = _keypair()
    ts, body = "1700000000", '{"type":1}'
    sig = sk.sign(f"{ts}{body}".encode()).signature.hex()
    assert discord.verify_signature(public_key=pub, signature=sig, timestamp=ts, body=body)
    # tamper
    assert not discord.verify_signature(public_key=pub, signature=sig, timestamp=ts,
                                        body=body + " ")
    assert not discord.verify_signature(public_key=pub, signature="00" * 64,
                                        timestamp=ts, body=body)


def test_command_text_extraction():
    payload = {"type": 2, "data": {"name": "twocustomer",
               "options": [{"name": "text", "value": "monitor Aurora Drinks"}]}}
    assert discord.command_text(payload) == "monitor Aurora Drinks"


def test_interactions_ping_pong():
    """A signed PING returns PONG; an unsigned request is rejected 401."""
    from fastapi.testclient import TestClient

    from app import config
    from app.main import app

    sk, pub = _keypair()
    # patch the public key into settings (cached)
    config.get_settings().discord_public_key = pub

    client = TestClient(app)
    body = json.dumps({"type": 1})
    ts = "1700000000"
    sig = sk.sign(f"{ts}{body}".encode()).signature.hex()

    r = client.post("/discord/interactions", content=body,
                    headers={"X-Signature-Ed25519": sig,
                             "X-Signature-Timestamp": ts,
                             "Content-Type": "application/json"})
    assert r.status_code == 200 and r.json() == {"type": 1}

    bad = client.post("/discord/interactions", content=body,
                      headers={"X-Signature-Ed25519": "00" * 64,
                               "X-Signature-Timestamp": ts})
    assert bad.status_code == 401
