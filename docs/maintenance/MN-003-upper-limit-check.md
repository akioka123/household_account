# MN-003: 変動費・固定費の上限件数チェックが未実装

## 事象

- 再現手順: 設定画面で `max_variable_items` / `max_fixed_items` を小さい値に変更したあと、月次画面でその上限を超える件数のカード請求行や固定費項目を登録する
- 期待結果: `docs/basic_design.md` 2.3.2「行数は設定で上限管理」のとおり、上限超過時は登録が拒否される
- 実際の結果: `Settings.max_variable_items` / `max_fixed_items` は保存されるだけで、`RegisterCardStatementsUseCase` にも `ManageFixedItemsUseCase.add_fixed_item` にも上限チェックが無く、無制限に登録できる

## 原因

- 両ユースケースとも `SettingsRepository` に依存しておらず、`Settings` を一切参照していなかった

## 方針

- ユーザー承認: 2026-08-27
- `RegisterCardStatementsUseCase.execute()`: 送信されたカード請求コマンド件数（`len(commands)`）が `max_variable_items` を超える場合に `ValueError` を送出
- `ManageFixedItemsUseCase.add_fixed_item()`: 既存の固定費項目数（`len(all_items)`）が `max_fixed_items` に達している場合に `ValueError` を送出
- 呼び出し元ルーターにtry/exceptは追加しない（`register_card_statements`・`add_fixed_item` の両エンドポイントとも、既存の他のValueError（カード不正・固定費項目不正など）も未捕捉のままであり、本修正はその既存の一貫性の範囲内）

## 修正

- `app/application/usecase/register_card_statements.py`: `settings_repo: SettingsRepository` を追加し、`execute()` 冒頭で件数チェック
- `app/application/usecase/manage_fixed_items.py`: `settings_repo: SettingsRepository` を追加し、`add_fixed_item()` で件数チェック
- `app/presentation/web/routers/month_router.py`: `provide_settings_repo` を追加し、`provide_register_card_statements_uc` / `provide_manage_fixed_items_uc` に配線
- テスト更新（コンストラクタにsettings_repoが増えたことに伴う既存テストの追従）
  - `tests/unit/application/test_register_card_statements.py`: `fake_settings_repo` フィクスチャ追加、UT-RCS-01（上限超過でValueError）を新規追加
  - `tests/unit/application/test_manage_fixed_items.py`: `fake_settings_repo` フィクスチャ追加、UT-MFI-01（上限超過でValueError）を新規追加
  - `tests/unit/application/test_fixed_item_history_upsert.py`: `_build_usecase` にsettings_repoモックを追加

## ミニ検証

- `ruff check`（変更ファイル一式）: 既存の未使用変数1件（`test_manage_fixed_items.py` の `ym`、本修正と無関係の既存指摘）を除き問題なし
- `pytest tests -q`: 126 passed（修正前123 + 新規3件、既存テストの回帰なし）
- 画面確認: なし（バックエンドのバリデーション追加のみ）

## 影響範囲

- `app/application/usecase/register_card_statements.py`
- `app/application/usecase/manage_fixed_items.py`
- `app/presentation/web/routers/month_router.py`
- `tests/unit/application/test_register_card_statements.py`
- `tests/unit/application/test_manage_fixed_items.py`
- `tests/unit/application/test_fixed_item_history_upsert.py`

## トレーサビリティ

- UT-RCS-01, UT-MFI-01 を追加
