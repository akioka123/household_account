# 証跡台帳: ゲート7 結合テスト（レシート金額抽出・生活費入力の詳細化）

- 検証者: verifier-test（第3層・検証系）
- 検証日: 2026-08-27
- 対象: `tests/integration/test_receipt_living_expense_items.py`（21ケース）

## 証跡の性質について

本結合テストは `docs/work-orders/7-integration-test-order.md` の指定どおり `TestClient` + `app.dependency_overrides` によるDBなし・実ブラウザなしの結合テストである（プロジェクトCLAUDE.mdの既存規約）。そのため実ブラウザ操作のスクリーンショットは対象外とし、実行ログを証跡とする。

## 実行ログ一覧

| ID | 操作 | 期待結果 | 実結果 | ログファイル |
|---|---|---|---|---|
| EV-01 | `pytest tests/integration -q` を実行 | 全件成功（新規21件を含む） | **32 passed** in 2.37s | `pytest-integration-20260827.log` |
| EV-02 | `pytest tests -q`（全体）を実行 | 回帰なし・全件成功 | **180 passed**, 30 warnings in 2.90s（builder-test報告値と一致） | `pytest-all-20260827.log` |
| EV-03 | `ruff check app tests` を実行 | 新規ファイルにエラーなし | 22 errors（すべて既存ファイルの既知エラー。新規テストファイルは0件） | `ruff-check-20260827.log` |

## 判定

詳細な判定根拠は `docs/verification/integration-test-result.md` を参照（ゲート7チェックリスト9項目すべてPASS、総合合格）。
