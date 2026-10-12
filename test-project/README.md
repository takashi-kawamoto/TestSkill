# ひらめきクイズ

FastAPIで動作する日本語の4択クイズアプリです。

- 問題数は1〜5問から選択できます。
- 1問ずつ回答し、最後にサーバーで採点します。
- 結果には正解数、各問題の正解・不正解、解説を表示します。
- スマートフォンにも対応し、何度でも挑戦できます。
- クイズ管理画面で問題の追加・編集・削除ができます。登録数は最大5問です。
- 問題はSQLiteに保存されるため、サーバー再起動後も保持されます。

## 起動（uv）

```powershell
uv sync
uv run uvicorn main:app --reload
```

ブラウザーで http://127.0.0.1:8000 を開きます。
問題の管理は http://127.0.0.1:8000/admin で行えます。
APIドキュメントは http://127.0.0.1:8000/docs です。

## 起動（pip / Python 3.13以上）

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

## テスト

```powershell
uv sync --group dev
uv run pytest
```

pipの場合は仮想環境にpytestとhttpxもインストールしてください。

## クイズ管理

- 管理画面と管理APIは、同じPC（`localhost`）からのみ操作できます。
- 問題は `data/quiz.sqlite3` に保存されます。`data/` はGit管理対象外です。
- 出題を始めた時点の問題内容を保存して採点するため、回答中に問題を編集・削除しても、出題時の正解と解説で結果を表示します。
- 問題が0件の場合はクイズを開始できません。管理画面から問題を追加してください。

## API

- `GET /api/questions?count=5`：1〜5問を取得（正解は含めません）。
- `POST /api/submit`：出題時に返る`session_id`と回答を送信して採点します。
- `GET /api/admin/questions`、`POST /api/admin/questions`、`PUT /api/admin/questions/{id}`、`DELETE /api/admin/questions/{id}`：問題を管理します（localhost限定）。

例：
```json
{"session_id": "GET /api/questions の session_id", "answers": [{"question_id": 1, "choice": 1}]}
```

出題APIは正解と解説を返さず、採点後にだけ表示します。

実装で参照した公式ドキュメント：
[静的ファイル](https://fastapi.tiangolo.com/tutorial/static-files/) /
[テスト](https://fastapi.tiangolo.com/tutorial/testing/)
