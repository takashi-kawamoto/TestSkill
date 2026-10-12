import ipaddress
import json
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

BASE_DIR = Path(__file__).resolve().parent
MAX_QUESTIONS = 5
SESSION_SECONDS = 86400

QUESTIONS = [
    {"id": 1, "text": "日本で最も高い山は？", "choices": ["北岳", "富士山", "槍ヶ岳", "阿蘇山"], "correct": 1, "explanation": "富士山は標高3,776メートルで、日本で最も高い山です。"},
    {"id": 2, "text": "水の化学式は？", "choices": ["CO₂", "O₂", "H₂O", "NaCl"], "correct": 2, "explanation": "水は水素原子2個と酸素原子1個からなり、H₂Oと表します。"},
    {"id": 3, "text": "太陽系で最も大きい惑星は？", "choices": ["地球", "火星", "土星", "木星"], "correct": 3, "explanation": "木星は太陽系で最も大きい惑星です。"},
    {"id": 4, "text": "1バイトは何ビット？", "choices": ["8ビット", "4ビット", "16ビット", "32ビット"], "correct": 0, "explanation": "1バイトは8ビットです。"},
    {"id": 5, "text": "三角形の内角の和は？", "choices": ["90度", "180度", "270度", "360度"], "correct": 1, "explanation": "平面上の三角形の内角の和は180度です。"},
]


class QuestionInput(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    choices: list[str] = Field(min_length=4, max_length=4)
    correct: int = Field(ge=0, le=3, strict=True)
    explanation: str = Field(min_length=1, max_length=4000)

    @field_validator("text", "explanation")
    @classmethod
    def nonblank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("空白のみの入力はできません。")
        return value

    @field_validator("choices")
    @classmethod
    def valid_choices(cls, values: list[str]) -> list[str]:
        values = [value.strip() for value in values]
        if any(not value or len(value) > 500 for value in values):
            raise ValueError("選択肢は1〜500文字で入力してください。")
        return values


class Answer(BaseModel):
    question_id: int = Field(strict=True)
    choice: int = Field(ge=0, le=3, strict=True)


class Submission(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    answers: list[Answer] = Field(min_length=1, max_length=MAX_QUESTIONS)


class Store:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            exists = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='questions'"
            ).fetchone()
            db.execute("CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, data TEXT NOT NULL, expires REAL NOT NULL)")
            if not exists:
                for question in QUESTIONS:
                    db.execute("INSERT INTO questions(id, data) VALUES (?, ?)",
                               (question["id"], json.dumps(question, ensure_ascii=False)))

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def list(self, db):
        return [dict(json.loads(row[1]), id=row[0])
                for row in db.execute("SELECT id, data FROM questions ORDER BY id")]


def require_local_admin(request: Request):
    host = request.url.hostname
    try:
        local = bool(request.client and ipaddress.ip_address(request.client.host).is_loopback)
    except ValueError:
        local = False
    if not local or host not in {"localhost", "127.0.0.1", "::1"}:
        raise HTTPException(403, "管理機能は同じPCからのみ利用できます。")
    origin = request.headers.get("origin")
    if origin:
        parsed = urlsplit(origin)
        if (parsed.scheme, parsed.netloc) != (request.url.scheme, request.url.netloc):
            raise HTTPException(403, "別サイトからの管理操作はできません。")
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "別サイトからの管理操作はできません。")


def create_app(db_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="ひらめきクイズ", version="1.1.0")
    store = Store(db_path or Path(os.environ.get("QUIZ_DB_PATH", BASE_DIR / "data" / "quiz.sqlite3")))
    app.state.store = store
    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

    @app.get("/", response_class=FileResponse)
    def index():
        return FileResponse(BASE_DIR / "static" / "index.html")

    @app.get("/admin", dependencies=[Depends(require_local_admin)])
    def admin():
        return FileResponse(BASE_DIR / "templates" / "admin.html")

    @app.get("/api/status")
    def status():
        with store.connection() as db:
            return {"available_questions": len(store.list(db)), "max_questions": MAX_QUESTIONS}

    @app.get("/api/questions")
    def questions(count: int = Query(default=5, ge=1, le=MAX_QUESTIONS)):
        with store.connection() as db:
            selected = store.list(db)[:count]
            if not selected:
                raise HTTPException(409, "問題が未登録です。管理画面から追加してください。")
            session_id = secrets.token_urlsafe(32)
            db.execute("DELETE FROM sessions WHERE expires < ?", (time.time(),))
            db.execute("INSERT INTO sessions VALUES (?, ?, ?)",
                       (session_id, json.dumps(selected, ensure_ascii=False), time.time() + SESSION_SECONDS))
        return {"questions": [{"id": q["id"], "text": q["text"], "choices": q["choices"]}
                              for q in selected],
                "max_questions": MAX_QUESTIONS, "session_id": session_id}

    @app.post("/api/submit")
    def submit(submission: Submission):
        with store.connection() as db:
            row = db.execute("SELECT data FROM sessions WHERE id=? AND expires>=?",
                             (submission.session_id, time.time())).fetchone()
        if row is None:
            raise HTTPException(409, "クイズの有効期限が切れました。最初から開始してください。")
        question_map = {q["id"]: q for q in json.loads(row[0])}
        ids = [answer.question_id for answer in submission.answers]
        if len(ids) != len(set(ids)) or set(ids) != set(question_map):
            raise HTTPException(422, "出題されたすべての問題に1回ずつ回答してください。")
        results = []
        for answer in submission.answers:
            question = question_map[answer.question_id]
            results.append({
                "question_id": question["id"], "text": question["text"],
                "selected_answer": question["choices"][answer.choice],
                "correct_answer": question["choices"][question["correct"]],
                "is_correct": answer.choice == question["correct"],
                "explanation": question["explanation"],
            })
        return {"score": sum(item["is_correct"] for item in results),
                "total": len(results), "results": results}

    @app.get("/api/admin/questions", dependencies=[Depends(require_local_admin)])
    def list_questions():
        with store.connection() as db:
            return {"questions": store.list(db), "max_questions": MAX_QUESTIONS}

    @app.post("/api/admin/questions", status_code=201, dependencies=[Depends(require_local_admin)])
    def add_question(question: QuestionInput):
        with store.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT COUNT(*) FROM questions").fetchone()[0] >= MAX_QUESTIONS:
                raise HTTPException(409, "登録できる問題は最大5問です。")
            cursor = db.execute("INSERT INTO questions(data) VALUES (?)",
                                (question.model_dump_json(),))
            return dict(question.model_dump(), id=cursor.lastrowid)

    @app.put("/api/admin/questions/{question_id}", dependencies=[Depends(require_local_admin)])
    def update_question(question_id: int, question: QuestionInput):
        with store.connection() as db:
            cursor = db.execute("UPDATE questions SET data=? WHERE id=?",
                                (question.model_dump_json(), question_id))
            if not cursor.rowcount:
                raise HTTPException(404, "問題が見つかりません。")
        return dict(question.model_dump(), id=question_id)

    @app.delete("/api/admin/questions/{question_id}", status_code=204,
                dependencies=[Depends(require_local_admin)])
    def delete_question(question_id: int):
        with store.connection() as db:
            if not db.execute("DELETE FROM questions WHERE id=?", (question_id,)).rowcount:
                raise HTTPException(404, "問題が見つかりません。")

    return app


app = create_app()
