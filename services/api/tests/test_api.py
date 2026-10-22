from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_mock_chat_matches_contract():
    r = client.post("/api/chat", json={"dataset_id": "demo", "question": "ทดสอบ"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in {"answered", "clarify", "refused", "error"}
    assert set(body) >= {"status", "answer", "steps", "table", "chart", "meta"}
    assert body["table"]["columns"] == ["จังหวัด", "ยอดขาย"]


def test_chat_rejects_empty_question():
    r = client.post("/api/chat", json={"dataset_id": "demo", "question": ""})
    assert r.status_code == 422
