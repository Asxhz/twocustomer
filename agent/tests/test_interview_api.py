"""P4.34 — interview endpoints: start → answer*N → insight (in-process state)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_interview_full_flow():
    sid = "iv-api-1"
    r = client.post("/interview/start",
                    json={"session_id": sid, "brand": "aurora-drinks",
                          "customer": "Rosie"})
    assert r.status_code == 200
    body = r.json()
    assert body["question"] and body["done"] is False
    total = body["progress"][1]

    insight = None
    for i in range(total):
        a = client.post("/interview/answer",
                        json={"session_id": sid,
                              "text": f"answer number {i} with some detail"})
        data = a.json()
        if data["done"]:
            insight = data["insight"]
            break
    assert insight is not None
    assert insight["title"].startswith("Interview")


def test_answer_unknown_session():
    r = client.post("/interview/answer", json={"session_id": "nope", "text": "x"})
    assert r.json().get("error")
