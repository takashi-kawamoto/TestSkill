from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="ひらめきクイズ", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# 正解番号は0始まり。問題は最大5問に制限する。
QUESTIONS = [
    {"id": 1, "text": "日本で最も高い山は？", "choices": ["北岳", "富士山", "槍ヶ岳", "阿蘇山"], "correct": 1, "explanation": "富士山は標高3,776メートルで、日本で最も高い山です。"},
    {"id": 2, "text": "水の化学式は？", "choices": ["CO₂", "O₂", "H₂O", "NaCl"], "correct": 2, "explanation": "水は水素原子2個と酸素原子1個からなり、H₂Oと表します。"},
    {"id": 3, "text": "太陽系で最も大きい惑星は？", "choices": ["地球", "火星", "土星", "木星"], "correct": 3, "explanation": "木星は太陽系で最も大きい惑星です。"},
    {"id": 4, "text": "1バイトは何ビット？", "choices": ["8ビット", "4ビット", "16ビット", "32ビット"], "correct": 0, "explanation": "1バイトは8ビットです。"},
    {"id": 5, "text": "三角形の内角の和は？", "choices": ["90度", "180度", "270度", "360度"], "correct": 1, "explanation": "平面上の三角形の内角の和は180度です。"},
]
MAX_QUESTIONS = 5
QUESTION_MAP = {q["id"]: q for q in QUESTIONS[:MAX_QUESTIONS]}


class Answer(BaseModel):
    question_id: int = Field(strict=True)
    choice: int = Field(ge=0, le=3, strict=True)


class Submission(BaseModel):
    answers: list[Answer] = Field(min_length=1, max_length=MAX_QUESTIONS)


@app.get("/", response_class=FileResponse)
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/questions")
def questions(count: int = Query(default=5, ge=1, le=MAX_QUESTIONS)):
    return {
        "questions": [
            {"id": q["id"], "text": q["text"], "choices": q["choices"]}
            for q in QUESTIONS[:count]
        ],
        "max_questions": MAX_QUESTIONS,
    }


@app.post("/api/submit")
def submit(submission: Submission):
    ids = [answer.question_id for answer in submission.answers]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=422, detail="同じ問題に複数回回答できません。")
    if any(question_id not in QUESTION_MAP for question_id in ids):
        raise HTTPException(status_code=422, detail="存在しない問題です。")
    results = []
    for answer in submission.answers:
        question = QUESTION_MAP[answer.question_id]
        results.append({
            "question_id": question["id"],
            "text": question["text"],
            "selected_answer": question["choices"][answer.choice],
            "correct_answer": question["choices"][question["correct"]],
            "is_correct": answer.choice == question["correct"],
            "explanation": question["explanation"],
        })
    score = sum(result["is_correct"] for result in results)
    return {"score": score, "total": len(results), "results": results}
