from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_home_and_assets():
    assert client.get("/").status_code == 200
    assert client.get("/static/app.js").status_code == 200


def test_question_limit_and_no_answer_leak():
    for count in (1, 5):
        questions = client.get(f"/api/questions?count={count}").json()["questions"]
        assert len(questions) == count
        assert all(set(q) == {"id", "text", "choices"} for q in questions)
    for count in (0, 6):
        assert client.get(f"/api/questions?count={count}").status_code == 422


def test_scoring():
    answers = [{"question_id": i, "choice": choice} for i, choice in enumerate([1, 2, 3, 0, 1], 1)]
    result = client.post("/api/submit", json={"answers": answers}).json()
    assert result["score"] == result["total"] == 5
    answers[0]["choice"] = 0
    result = client.post("/api/submit", json={"answers": answers}).json()
    assert result["score"] == 4
    assert result["results"][0]["correct_answer"] == "富士山"
    assert result["results"][0]["is_correct"] is False


def test_invalid_submissions():
    valid = {"question_id": 1, "choice": 1}
    for answers in ([], [valid] * 6, [valid, valid],
                    [{"question_id": 99, "choice": 0}],
                    [{"question_id": 1, "choice": 4}],
                    [{"question_id": 1, "choice": -1}],
                    [{"question_id": 1, "choice": True}]):
        assert client.post("/api/submit", json={"answers": answers}).status_code == 422
