# FastAPI 単体試験仕様書（OpenAPIスキーマ起点）

> **利用方法**: 承認済みの `unit_test_viewpoints.md` からテストケースを展開する。`{{...}}` を実プロジェクトの情報で置換する。下記の `POST /items` は架空の例であり、実スキーマの仕様を表すものではない。

## 1. 文書管理

| 項目 | 内容 |
|---|---|
| 文書ID | `UT-SPEC-{{system}}-{{version}}` |
| システム名 / 対象サービス | {{システム名}} / {{サービス名}} |
| 対象API / タグ | {{対象API}} |
| OpenAPI取得元 / SHA-256 | {{ファイルパスまたはURL}} / {{ハッシュ値}} |
| 対象Gitコミット | {{コミットSHA}} |
| 対応試験観点一覧 | `{{unit_test_viewpoints.md}}`（版: {{版}}） |
| 参照要件・設計 | {{要件ID / 詳細設計書}} |
| 作成者 / 作成日 | {{担当者}} / {{YYYY-MM-DD}} |
| レビュー担当 / 承認日 | {{担当者}} / {{YYYY-MM-DD}} |
| 状態 | 草案 / レビュー中 / 承認済み |

## 2. 試験方針

- **目的**: FastAPIエンドポイントの入力検証・ルーティング・レスポンス契約・依存先呼び出し・例外変換を検証する。
- **単体試験の境界**: `{{対象router/handler/service}}`。DB、外部HTTP、メッセージキュー、時計等は必要に応じてモック化する。
- **ツール**: Python {{version}}, FastAPI {{version}}, Pydantic {{version}}, pytest {{version}}, httpx {{version}}, uv。
- **実行例**: `uv run pytest tests/unit -v`。
- **基本原則**: テストの期待値はOpenAPIおよび承認済み設計から定義し、実装の現状に合わせて変更しない。
- **注記**: `422` はFastAPIの一般的な入力検証応答だが、例外ハンドラ等で変更可能。実際の契約と設定を確認して採用する。

## 3. テスト環境・依存関係

| 項目 | 設定・方針 |
|---|---|
| アプリ生成 | `{{app.main:create_app}}` または `{{app.main:app}}` |
| HTTPクライアント | `fastapi.testclient.TestClient` または `httpx.AsyncClient` + `ASGITransport` |
| DBアクセス | `app.dependency_overrides[{{get_db}}] = {{fake_db}}` |
| 認証依存 | `{{get_current_user}}` を正常/異常ごとに切替（認証自体を試す場合はoverrideしない） |
| 外部API | `{{Mock/AsyncMockの差し込み先}}` |
| 状態初期化 | 各テスト前後でoverride・モック・テストデータを初期化 |
| 時刻・乱数 | 必要に応じて固定 |
| テストデータ | `tests/fixtures/{{...}}` |
| 試験実行条件 | {{環境変数、設定値など}} |

## 4. 対象APIの契約情報

| 項目 | 値 |
|---|---|
| 操作ID | API-001 |
| operationId | `create_item` |
| HTTPメソッド / パス | POST `/items` |
| Request Content-Type | `application/json`（スキーマで確認） |
| Request Schema | `#/components/schemas/ItemCreate` |
| Response Schema | `#/components/schemas/ItemRead` |
| 定義済みレスポンス | `201`, `422`（例） |
| Security | {{方式 / スコープ}} |
| 実装対象 | `{{app.api.items:create_item}}` |
| スキーマ根拠 | `paths./items.post` |

## 5. テストケース一覧

| テストID | 観点ID | ケース名 | 分類 | 入力・条件 | 期待HTTPステータス | 期待レスポンス/副作用 | pytest関数 | 仕様確定 | 状態 |
|---|---|---|---|---|---|---|---|---|---|
| TC-API001-001 | VP-API001-001 | 正常な作成要求 | 正常系 | 有効JSON、サービスモック成功 | 201（例） | `ItemRead`に適合、サービス呼び出し1回 | `test_tc_api001_001_create_success` | 要確認 | 未実装 |
| TC-API001-002 | VP-API001-002 | 必須フィールド欠落 | 異常系 | `{{field}}`を省略 | 422（標準構成の場合） | バリデーションエラー、サービス未呼出 | `test_tc_api001_002_missing_field` | 要確認 | 未実装 |
| TC-API001-003 | VP-API001-003 | 正常応答の型検証 | 契約 | 有効JSON、サービスモック成功 | 201（例） | 必須項目・型・Content-Typeが契約どおり | `test_tc_api001_003_response_schema` | 要確認 | 未実装 |
| TC-API001-004 | VP-API001-004 | 認証情報欠落 | 認証 | Authorizationヘッダーなし | {{設計確認}} | {{認証エラー形式}} | `test_tc_api001_004_no_auth` | 未確定 | 保留 |
| TC-{{...}} | VP-{{...}} | {{ケース名}} | {{分類}} | {{入力}} | {{ステータス}} | {{期待結果}} | `test_tc_...` | 確定/要確認 | 未実装 |

## 6. 詳細テストケース記述テンプレート

### TC-{{操作ID}}-{{連番}}: {{ケース名}}

| 項目 | 記載内容 |
|---|---|
| テストID | `TC-{{...}}` |
| 対応観点ID | `VP-{{...}}` |
| 要件ID | `REQ-{{...}}` |
| 操作ID / operationId | `API-{{...}}` / `{{operationId}}` |
| 分類 / 優先度 | 正常系・異常系・境界値・認証等 / 高・中・低 |
| 対象関数 | `{{module:function}}` |
| 試験目的 | {{何を保証するか}} |
| 根拠 | {{OpenAPI JSON Pointer、設計書の節、要件ID}} |
| 前提条件 | {{認証状態、依存関係、設定、事前データ}} |
| モック設定 | {{差し込み先、返却値、例外、副作用}} |
| HTTPメソッド / パス | {{GET/POST...}} `{{/path}}` |
| Path / Query / Header / Cookie | {{各入力値、未指定の場合はその旨}} |
| Content-Type / Request Body | {{メディアタイプ、JSON等の具体値}} |
| 実行手順 | 1. モック準備 → 2. HTTP要求 → 3. レスポンス・呼出検証 |
| 期待HTTPステータス | {{数値と根拠}} |
| 期待レスポンス | {{JSON、ヘッダー、型、必須キー、値}} |
| 期待副作用 | {{DB保存相当の呼出回数・引数、未呼出条件}} |
| 後処理 | {{dependency_overrides解除、状態復元}} |
| pytest関数名 | `test_tc_{{...}}` |
| 仕様確定度 | 確定 / 要確認 |
| レビュー結果 | 未レビュー / 承認 / 差戻し |

#### 具体的なリクエスト・期待レスポンス（ケースごとに記載）

**入力例**（実際のOpenAPIスキーマに合わせて置換）:

```json
{
  "name": "example-item"
}
```

**期待レスポンス例**（フィールド名・値は承認済み仕様に合わせて置換）:

```json
{
  "id": 123,
  "name": "example-item"
}
```

**期待するモック呼び出し**:

```text
{{service.create_item}}(name="example-item") -> {{Item(id=123, name="example-item")}}
呼び出し回数: 1
```

## 7. 境界値・異常系ケースの展開ルール

| スキーマ要素 | 代表的な試験データ | 注意事項 |
|---|---|---|
| `required` | 指定あり / 欠落 | 省略と明示的nullを区別 |
| `type: integer/number` | 0、負数、上下限、上下限±1 | 制約がない場合は拒否を期待しない |
| `minimum/maximum` | 境界の内側・境界・外側 | exclusive指定を考慮 |
| `minLength/maxLength` | 0、境界±1、Unicode | 文字数とバイト数を混同しない |
| `pattern` | 一致 / 不一致 | 正規表現の仕様差を確認 |
| `enum` | 各有効値 / 無効値 | 型変換や大小文字の扱いを確認 |
| `format` | 妥当 / 不正形式 | `format`の実際の検証強度を確認 |
| `array` | 空 / 1件 / 境界件数 / 要素型不正 | `uniqueItems`等を確認 |
| `oneOf/anyOf` | 各分岐 / 不一致 / 複数一致 | Pydantic実装との対応を確認 |
| `additionalProperties` | 未定義キー追加 | Pydanticの`extra`設定を確認 |
| `security` | 有効 / 欠落 / 不正 / 権限不足 | 401/403等は実装により異なる |
| `responses` | 各定義ステータス | 発生条件は詳細設計で補完 |

## 8. pytest実装ひな形

```python
"""TC-API001-001: 正常な作成要求（サンプル。対象アプリに合わせて修正）"""
from fastapi.testclient import TestClient

# from app.main import app
# from app.dependencies import get_service


def test_tc_api001_001_create_success(client: TestClient, mock_service):
    # Arrange: fixture側で依存関係を差し替え、返却値を固定する
    mock_service.create_item.return_value = {"id": 123, "name": "example-item"}

    # Act
    response = client.post("/items", json={"name": "example-item"})

    # Assert: 実際のOpenAPI/設計に合わせて期待値を確定する
    assert response.status_code == 201
    assert response.json() == {"id": 123, "name": "example-item"}
    mock_service.create_item.assert_called_once()
```

> `client` / `mock_service` はプロジェクト固有のfixtureとして定義する。上記は実行可能な完成品ではなく、生成指示用のひな形。

## 9. テスト実行・結果記録

| テストID | pytest関数 | Red確認 | Green確認 | 最終結果 | 実行日 | 証跡 |
|---|---|---|---|---|---|---|
| TC-API001-001 | `test_tc_api001_001_create_success` | 未実施 | 未実施 | 未実施 | {{日付}} | {{CI URL / ログ}} |

実行コマンド例:

```bash
uv run pytest tests/unit -v
uv run pytest tests/unit --cov=app --cov-report=term-missing
```

## 10. トレーサビリティと整合性

- [ ] すべての承認済み観点IDに対応するケースが存在する。
- [ ] 各ケースにテストID、根拠、具体的入力、期待値、モック条件がある。
- [ ] テストIDとpytest関数が1対1または明示した1対多で対応する。
- [ ] OpenAPIのレスポンス定義と期待ステータス・本文が整合する。
- [ ] 業務ロジック・DB副作用の期待値は承認済み設計で裏付けられる。
- [ ] 要確認のケースを確定扱いしていない。
- [ ] テストコード作成前に人間のレビューを受けた。

## 11. 未確定事項・レビュー指摘

| 課題ID | 関連テストID | 内容 | 影響 | 確認先 | 決定事項 | 状態 |
|---|---|---|---|---|---|---|
| Q-001 | TC-API001-004 | 認証失敗時のHTTPステータスが未確定 | Assert確定不可 | {{担当者}} | {{未記入}} | 未解決 |

## 12. 承認ゲート（G2）

| レビュアー | 判定 | 日付 | コメント |
|---|---|---|---|
| {{氏名}} | 承認 / 条件付き承認 / 差戻し | {{日付}} | {{コメント}} |

**実装開始条件**: G2承認済みであり、実装対象ケースの期待値が確定していること。未確定ケースは保留し、人間の判断を求める。
