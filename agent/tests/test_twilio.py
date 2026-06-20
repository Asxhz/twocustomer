"""V2 Twilio — signature verify + SMS/voice interview TwiML flow."""

import base64
import hashlib
import hmac

from fastapi.testclient import TestClient

from app.channels import twilio
from app.main import app

client = TestClient(app)
TOKEN = "test-twilio-token"


def _sign(url, params):
    base = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    return base64.b64encode(
        hmac.new(TOKEN.encode(), base.encode(), hashlib.sha1).digest()).decode()


def test_verify_signature_good_bad():
    url, params = "https://x/twilio/sms", {"From": "+1", "Body": "hi"}
    sig = _sign(url, params)
    assert twilio.verify_signature(auth_token=TOKEN, signature=sig, url=url, params=params)
    assert not twilio.verify_signature(auth_token=TOKEN, signature="bad", url=url, params=params)


def test_twiml_builders():
    m = twilio.twiml_message("hello & welcome")
    assert "<Message>hello &amp; welcome</Message>" in m
    g = twilio.twiml_say_gather("Q1?", action="https://x/g")
    assert 'input="speech"' in g and "https://x/g" in g
    end = twilio.twiml_say_gather("bye", action="", end=True)
    assert "<Hangup/>" in end


def test_sms_interview_flow(monkeypatch):
    monkeypatch.setattr(twilio, "verify_signature", lambda **k: True)
    # first inbound starts the interview
    r1 = client.post("/twilio/sms", data={"From": "+15550001111", "Body": "hello"})
    assert r1.status_code == 200 and "<Message>" in r1.text and "?" in r1.text
    # subsequent answers advance it
    r2 = client.post("/twilio/sms", data={"From": "+15550001111", "Body": "better tone"})
    assert r2.status_code == 200 and "<Message>" in r2.text


def test_sms_rejects_bad_signature():
    r = client.post("/twilio/sms", data={"From": "+1", "Body": "x"})
    assert r.status_code == 403  # no valid signature


def test_voice_starts_interview(monkeypatch):
    monkeypatch.setattr("app.main._twilio_verified", lambda *a, **k: True)
    r = client.post("/twilio/voice", data={"From": "+15550002222"})
    assert r.status_code == 200
    assert 'input="speech"' in r.text and "TwoCustomer" in r.text
