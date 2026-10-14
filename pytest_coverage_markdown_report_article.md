# pytest実行結果とカバレッジ結果からMarkdown報告書を自動生成する仕組み

## 1. はじめに

FastAPIなどのPython
Webアプリケーションでは、単体テストを実行するだけでなく、結果を人間がレビューできる形式で記録することが重要です。本記事では、`uv`、`pytest`、`pytest-cov`、`coverage.py`
を使い、テスト結果とカバレッジ計測結果を解析してMarkdown報告書を自動生成する設計を解説します。

目標は次の2ファイルを生成することです。

-   `04_test_results.md`：単体試験結果報告書
-   `05_coverage_report.md`：コードカバレッジ報告書

AIに集計値を推測させるのではなく、機械的に取得した一次データから決定論的に報告書を生成します。

## 2. 全体アーキテクチャ

``` mermaid
flowchart TD
    A[対象Pythonプロジェクト] --> B[pytest]
    B --> C[JUnit XML]
    B --> D[pytest-cov / coverage.py]
    D --> E[Coverage JSON]
    C --> F[test-report CLI]
    E --> F
    G[試験IDマッピング] --> F
    F --> H[単体試験結果報告書 Markdown]
    F --> I[カバレッジ報告書 Markdown]
```

実行と解析を分離し、JUnit XMLとCoverage
JSONを一次データとして保存します。これにより、テストを再実行せずに報告書を再生成できます。

## 3. 推奨技術スタック

  ツール                 用途
  ---------------------- ------------------------------------
  `uv`                   Python環境・依存関係管理
  `pytest`               単体テスト実行
  `pytest-cov`           pytestからカバレッジを計測
  `coverage.py`          行・分岐カバレッジの集計とJSON出力
  `httpx`                FastAPIのAPIテスト
  `pytest-asyncio`       非同期テスト
  `Typer`                CLI実装
  `Jinja2`               Markdownテンプレート描画
  Python標準ライブラリ   XML・JSON解析

対象プロジェクトの導入例：

``` bash
uv add --dev pytest pytest-cov coverage pytest-asyncio httpx
```

## 4. テスト実行と計測

``` bash
uv run pytest tests/unit/ \
  --junitxml=reports/raw/junit.xml \
  --cov=app \
  --cov-branch \
  --cov-report=json:reports/raw/coverage.json \
  --cov-report=html:reports/coverage-html
```

`app`
は実際のパッケージ名に置き換えてください。出力先ディレクトリを事前に作成しておきます。

-   **JUnit
    XML**：テストケース名、成功・失敗・エラー・スキップ、実行時間、失敗メッセージを解析するために使用します。
-   **Coverage
    JSON**：ファイル別の実行行、未実行行、分岐情報、集計値を解析するために使用します。
-   **HTMLカバレッジ**：開発者がコード上の未実行箇所を視覚的に確認するための補助資料です。

テストが失敗しても、生成済みの一次データから報告書を作成できるようにします。

## 5. 共通CLIツールの設計

複数のPythonプロジェクトから利用する独立CLI `test-report`
として実装します。

``` text
test-report/
├── pyproject.toml
├── src/test_report/
│   ├── cli.py
│   ├── runner.py
│   ├── parsers/
│   │   ├── junit_parser.py
│   │   └── coverage_parser.py
│   ├── analyzers/
│   │   ├── test_analyzer.py
│   │   └── coverage_analyzer.py
│   ├── generators/
│   │   ├── test_report.py
│   │   └── coverage_report.py
│   └── templates/
│       ├── test_results.md.j2
│       └── coverage_report.md.j2
└── tests/
    ├── test_junit_parser.py
    ├── test_coverage_parser.py
    └── test_generators.py
```

### 5.1 CLIコマンド

既存データから報告書を生成：

``` bash
uv run test-report generate \
  --junit reports/raw/junit.xml \
  --coverage reports/raw/coverage.json \
  --output docs/testing/unit/
```

テスト実行から報告書生成まで一括実行：

``` bash
uv run test-report run \
  --project . \
  --tests tests/unit/ \
  --source app \
  --output docs/testing/unit/
```

上記は**実装予定のCLIインターフェース例**であり、pytest標準のコマンドではありません。

### 5.2 内部処理

1.  `runner.py` がpytestを子プロセスとして実行する。
2.  `junit_parser.py` がJUnit
    XMLを解析し、ケース単位の結果を正規化する。
3.  `coverage_parser.py` がCoverage
    JSONを解析し、ファイル別・全体の計測値を正規化する。
4.  `analyzers/` が合否判定、未実行行の抽出、閾値判定を行う。
5.  `generators/`
    がJinja2テンプレートにデータを渡し、Markdownを出力する。
6.  テスト失敗時も可能な範囲で報告書を生成し、CLIの終了コードに失敗を反映する。

XMLは信頼できる入力として扱わず、外部実体参照などの安全性に配慮したパーサーを採用します。

## 6. 単体試験結果報告書の設計

出力先：`docs/testing/unit/04_test_results.md`

記載項目：

  セクション           内容
  -------------------- ------------------------------------------------------
  実行情報             実行日時、対象プロジェクト、Python・pytestバージョン
  サマリー             総件数、成功、失敗、エラー、スキップ
  成功率               成功 ÷ (成功 + 失敗 + エラー)
  失敗一覧             試験ID、テスト名、失敗理由、例外概要
  全ケース一覧         ケース単位の結果、実行時間
  試験仕様書との対応   試験ID、pytest nodeid、API、試験観点
  総合判定             合格・不合格・計測不成立

**報告書例（架空の数値）**

``` markdown
# 単体試験結果報告書

- 実行日時: 2026-10-14
- 対象: FastAPI Webアプリケーション

| 指標 | 件数 |
|---|---:|
| 総件数 | 150 |
| 成功 | 143 |
| 失敗 | 5 |
| エラー | 0 |
| スキップ | 2 |

- 成功率: 96.6%（143 / 148）
- 総合判定: 不合格

## 失敗テスト一覧

| 試験ID | pytest nodeid | 結果 |
|---|---|---|
| UT-API-003 | tests/unit/test_api.py::test_create_user | FAIL |
```

pytestの`nodeid`と業務上の試験IDは同一ではありません。試験仕様書とのトレーサビリティを実現するため、試験IDをpytestのマーカー、JUnit
XMLのプロパティ、または専用マッピングファイルで管理します。どの方式でも重複や未対応を検出します。

## 7. カバレッジ報告書の設計

出力先：`docs/testing/unit/05_coverage_report.md`

記載項目：

  セクション       内容
  ---------------- --------------------------------------------
  計測条件         対象ソース、除外設定、分岐計測の有無
  全体集計         Statement Coverage、Branch Coverage
  閾値判定         指標別の基準値と合否
  ファイル別集計   対象行数、実行行数、未実行行数、カバレッジ
  未実行箇所       ファイルパス、未実行行番号・範囲
  未網羅分岐       分岐元と未実行の分岐先
  総合判定         合格・不合格・計測不成立

**報告書例（架空の数値）**

``` markdown
# コードカバレッジ報告書

| 指標 | 実績 | 基準 | 判定 |
|---|---:|---:|---|
| Statement Coverage | 87.5% | 80% | 合格 |
| Branch Coverage | 78.2% | 80% | 不合格 |

## ファイル別カバレッジ

| ファイル | Statement Coverage | 未実行行 |
|---|---:|---|
| app/api/users.py | 95% | 45-48 |
| app/services/user_service.py | 88% | 72-81 |
| app/repositories/user.py | 72% | 30-42 |
```

coverage.pyの`percent_covered`は設定により行と分岐を合わせた総合指標となるため、**Statement
CoverageとBranch
Coverageを同じ値として扱ってはいけません**。JSONに含まれる行数・分岐数から別々に算出します。分岐計測が無効な場合はBranch
Coverageを「未計測」と表示し、0%とは区別します。

## 8. 品質ゲートの例

  項目                 合格条件
  -------------------- --------------------------------------------
  テスト実行           失敗・エラー0件
  テスト収集           1件以上
  Statement Coverage   80%以上
  Branch Coverage      80%以上
  試験ID対応           必須試験ケースの未対応0件
  データ整合性         JUnit XML・Coverage JSONが正常に解析できる
  報告書               Markdown2ファイルの生成成功

閾値はプロジェクト設定で変更可能にします。スキップやxfail/xpassの扱い、除外対象ファイル、分母の定義も明示します。カバレッジが高くてもテストの妥当性を保証するわけではないため、試験観点のレビューは別途実施します。

## 9. 出力ディレクトリの例

``` text
project/
├── app/
├── tests/
│   └── unit/
├── reports/
│   ├── raw/
│   │   ├── junit.xml
│   │   └── coverage.json
│   └── coverage-html/
│       └── index.html
└── docs/
    └── testing/
        └── unit/
            ├── 01_test_viewpoints.md
            ├── 02_test_viewpoint_matrix.md
            ├── 03_test_specification.md
            ├── 04_test_results.md
            └── 05_coverage_report.md
```

`01`〜`03`は人間によるレビュー対象の試験設計資料、`04`〜`05`は実行データから生成される報告書です。

## 10. 実装上の注意点

-   **実行失敗とレポート生成失敗を区別**する：テスト失敗時でもレポートを生成し、適切な終了コードを返します。
-   **古いデータの混入を防止**する：実行ごとに専用ディレクトリを作るか、実行IDで一次データを関連付けます。
-   **パスを正規化**する：OSごとの区切り文字や作業ディレクトリの差を吸収します。
-   **機密情報を保護**する：失敗ログや例外メッセージに含まれるトークン・個人情報をマスクします。
-   **並列実行に対応**する：pytest-xdistなどの利用時も結果を重複集計しないようにします。
-   **再現性を確保**する：実行日時、GitコミットID、テスト設定、依存関係の情報を保存します。
-   **結果の欠損を明示**する：XMLやJSONが存在しない場合は計測不成立とし、成功扱いにしません。

## 11. 開発ロードマップ

  フェーズ   実装内容
  ---------- --------------------------------------------------
  Phase 1    JUnit XML・Coverage JSONのパーサーとMarkdown生成
  Phase 2    pytest実行を含むCLI一括実行、品質ゲート
  Phase 3    試験仕様書・API・試験観点との対応付け
  Phase 4    前回比較、カバレッジ増減、回帰テスト結果の分析
  Phase 5    GitHub Actions等のCI連携

最初は**既存の計測ファイルを解析する機能**から実装するのが合理的です。これにより、レポート生成処理をpytest実行処理から独立して単体テストできます。

## 12. まとめ

`pytest`で実行し、`JUnit XML`と`Coverage JSON`を一次データとして保存し、独立CLIでMarkdownに変換する構成が有効です。人間向けの試験観点一覧・試験仕様書と実行結果を試験IDで紐づけることで、AIテスト駆動開発におけるレビュー可能性、追跡可能性、再現性を高められます。
