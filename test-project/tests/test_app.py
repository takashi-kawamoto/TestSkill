from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.fixture
def client(tmp_path: Path):
    return TestClient(
        create_app(tmp_path / "quiz.sqlite3"),
        base_url="http://localhost",
        client=("127.0.0.1", 50000),
    )


def test_home_and_assets(client):
    assert client.get("/").status_code == 200
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/admin").status_code == 200
    assert client.get("/static/admin.js").status_code == 200


def test_question_limit_and_no_answer_leak(client):
    for count in (1, 5):
        payload = client.get(f"/api/questions?count={count}").json()
        questions = payload["questions"]
        assert len(questions) == count
        assert payload["session_id"]
        assert all(set(q) == {"id", "text", "choices"} for q in questions)
    for count in (0, 6):
        assert client.get(f"/api/questions?count={count}").status_code == 422


def test_scoring(client):
    quiz = client.get("/api/questions?count=5").json()
    answers = [{"question_id": i, "choice": choice} for i, choice in enumerate([1, 2, 3, 0, 1], 1)]
    result = client.post("/api/submit", json={"session_id": quiz["session_id"], "answers": answers}).json()
    assert result["score"] == result["total"] == 5
    answers[0]["choice"] = 0
    result = client.post("/api/submit", json={"session_id": quiz["session_id"], "answers": answers}).json()
    assert result["score"] == 4
    assert result["results"][0]["correct_answer"] == "富士山"
    assert result["results"][0]["is_correct"] is False


def test_invalid_submissions(client):
    session_id = client.get("/api/questions?count=1").json()["session_id"]
    valid = {"question_id": 1, "choice": 1}
    for answers in ([], [valid] * 6, [valid, valid],
                    [{"question_id": 99, "choice": 0}],
                    [{"question_id": 1, "choice": 4}],
                    [{"question_id": 1, "choice": -1}],
                    [{"question_id": 1, "choice": True}]):
        assert client.post("/api/submit", json={"session_id": session_id, "answers": answers}).status_code == 422


def test_admin_crud_validation_and_limit(client):
    questions = client.get("/api/admin/questions").json()["questions"]
    first_id = questions[0]["id"]
    invalid = {"text": "  ", "choices": ["A", "B", "C", "D"], "correct": 1, "explanation": "解説"}
    assert client.post("/api/admin/questions", json=invalid).status_code == 422
    update = {"text": "更新した問題", "choices": ["A", "B", "C", "D"], "correct": 2, "explanation": "更新した解説"}
    saved = client.put(f"/api/admin/questions/{first_id}", json=update).json()
    assert saved["id"] == first_id
    assert client.get("/api/admin/questions").json()["questions"][0]["text"] == "更新した問題"
    assert client.post("/api/admin/questions", json=update).status_code == 409
    assert client.delete(f"/api/admin/questions/{first_id}").status_code == 204
    created = client.post("/api/admin/questions", json=update)
    assert created.status_code == 201
    assert created.json()["id"] != first_id


def test_quiz_snapshot_survives_edit_delete_and_restart(tmp_path: Path):
    database = tmp_path / "quiz.sqlite3"
    client = TestClient(create_app(database), base_url="http://localhost", client=("127.0.0.1", 50000))
    quiz = client.get("/api/questions?count=1").json()
    question_id = quiz["questions"][0]["id"]
    original = client.get("/api/admin/questions").json()["questions"][0]
    replacement = {"text": "変更後", "choices": ["1", "2", "3", "4"], "correct": 0, "explanation": "変更後の解説"}
    assert client.put(f"/api/admin/questions/{question_id}", json=replacement).status_code == 200
    restarted = TestClient(create_app(database), base_url="http://localhost", client=("127.0.0.1", 50000))
    assert restarted.get("/api/admin/questions").json()["questions"][0]["text"] == "変更後"
    result = restarted.post("/api/submit", json={"session_id": quiz["session_id"], "answers": [{"question_id": question_id, "choice": original["correct"]}]}).json()
    assert result["score"] == 1
    assert result["results"][0]["text"] == original["text"]
