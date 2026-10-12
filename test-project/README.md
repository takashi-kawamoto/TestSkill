# ひらめきクイズ

FastAPIで動作する日本語の4択クイズアプリです。

- 問題数は1〜5問から選択できます。
- 1問ずつ回答し、最後にサーバーで採点します。
- 結果には正解数、各問題の正解・不正解、解説を表示します。
- スマートフォンにも対応し、何度でも挑戦できます。
- サンプル問題5問を内蔵しています。データベースは不要です。

## 起動（uv）

```powershell
uv sync
uv run uvicorn main:app --reload
```

ブラウザーで http://127.0.0.1:8000 を開きます。
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

## API

- `GET /api/questions?count=5`：1〜5問を取得（正解は含めません）。
- `POST /api/submit`：回答を採点。回答は1〜5件、選択肢は0〜3。
  問題IDの重複、不明な問題ID、不正な選択肢は422エラーになります。

例：
```json
{"answers": [{"question_id": 1, "choice": 1}]}
```

問題の編集は`main.py`の`QUESTIONS`で行います。
回答や結果は保存されません。サンプルの学習用アプリです。

実装で参照した公式ドキュメント：
[静的ファイル](https://fastapi.tiangolo.com/tutorial/static-files/) /
[テスト](https://fastapi.tiangolo.com/tutorial/testing/)
