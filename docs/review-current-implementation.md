# household_account 実装精査結果

精査日: 2026-08-26
対象: app/ 以下、tests/ 以下（実装・テストを反復中の段階）

**全14件（重大2・中5・軽微7）対応済み（2026-08-27、hotfix-flow）。詳細は [docs/maintenance/MN-001](maintenance/MN-001-fixed-expenses-by-card-duplicate.md)〜[MN-011](maintenance/MN-011-get-db-skip-commit-on-get.md) を参照。**

## 重大

1. `app/domain/model/fixed_expenses.py:53-65`（`by_card()`）— `get_effective_histories()` を使わず `self.histories` をそのまま合計している。同一固定費項目に複数の改定履歴（`effective_from` 違い）があると、過去分まで二重集計される。`calculate()` は最新履歴のみを正しく集計するのに `by_card()` だけ非対応。CLAUDE.mdの中核式「カード変動費＝カード請求総額－カードに含まれる固定費」が壊れる。`app/application/usecase/get_month_summary.py:79` と `app/infrastructure/persistence/repositories/sqlalchemy_month_summary_repository.py:87` の両方で使われるため、月次画面・年次ダッシュボード双方に波及する。

2. 金額「0以上」バリデーションが全レイヤーで欠落。`Money.__post_init__`（`app/domain/model/money.py:13-19`）は `pass` のみで何も検証しない。`app/presentation/web/routers/month_router.py` の `Form(...)` にも `ge=0` 等の制約が無く（収入・現金・引出・カード請求・生活費・固定費履歴の各金額入力）、Command/Usecase層（`register_income.py`, `manage_cash.py`, `manage_fixed_items.py`, `manage_living_expenses.py`）でも未検証。`docs/basic_design.md` 2.3.2/2.3.3/2.3.5 の必須要件「金額は0以上」が未実装で、負値がそのままDBに保存される。

## 中

3. 月次サマリ計算ロジック（固定費合計・カード変動費・現金支出・損益）が `GetMonthSummaryUseCase`（application層）と `SqlAlchemyMonthSummaryRepository`（infrastructure層、`_calculate_summary`）にほぼ同一のコードで重複実装されている。重大#1の `by_card()` バグが両方に存在していたことがこの重複のリスクを裏付ける。CLAUDE.mdの層分離規約上、集計はdomain/serviceかusecaseに一本化すべき。

4. `Settings.max_variable_items` / `max_fixed_items` が保存されるだけで、カード請求登録・固定費履歴追加のどちらでも上限チェックが行われていない。`docs/basic_design.md` 2.3.2「行数は設定で上限管理（初期最大20件）」が未実装（`RegisterCardStatementsUseCase`, `ManageFixedItemsUseCase` ともに設定値を参照していない）。

5. `app/presentation/web/routers/month_router.py:578`（`register_card_statements`）— `amount_val > 0` でフィルタしているため、0円を入力した行は保存されずサイレントに無視される。既存の請求額を0に訂正する手段が無く、エラー表示も無い。

6. `/dashboard/overall`（総合ダッシュボード、`app/presentation/web/routers/dashboard_router.py:110-142`、`app/application/usecase/get_overall_dashboard_data.py`）が `docs/basic_design.md` に一切記載が無い。設計書と実装の乖離。

7. 重大#1（`by_card()` バグ）を検出できるテストが存在しない。`tests/unit/domain/test_fixed_expenses.py` の `test_by_card_aggregates_only_included_in_card` も `tests/unit/application/test_get_month_summary.py` も、同一固定費項目に複数の改定履歴があるケースを1件も検証していない。

## 軽微

8. `ruff check app tests` で22件のエラー（F401 未使用import 19件、F841 未使用変数3件）。0エラーの基準を満たさない。対象: `sqlalchemy_cash_balance_repository.py`, `sqlalchemy_fixed_item_history_repository.py`, `sqlalchemy_fixed_item_repository.py`, `sqlalchemy_income_repository.py`（F841含む）, `sqlalchemy_living_expense_repository.py`, `sqlalchemy_month_summary_repository.py`, `sqlalchemy_settings_repository.py`, `sqlalchemy_withdrawal_repository.py`, `helpers.py`, `test_get_dashboard_data.py`, `test_manage_fixed_items.py`（F841 2件）, `test_income.py`, `test_structured_logger.py`。

9. `app/presentation/web/routers/month_router.py` — `get_active_fixed_items_at` の重複呼び出し（786/792行, 832/833行, 894/895行）、`card_id_int` の二重代入（872/873行）などコピペ起因の無駄なDB呼び出し・重複コード。

10. `dashboard_router.py` / `month_router.py` / `settings_router.py` の各ハンドラのほぼ全てで `from fastapi.templating import Jinja2Templates` と `Jinja2Templates(directory=...)` をリクエスト毎に再生成している（`fixed_items_router.py` はモジュールレベルで1回だけ生成しており対照的）。

11. `app/presentation/web/helpers.py:7` — 戻り値型ヒント `dict[str, any]` の `any` は組み込み関数。`typing.Any` の書き間違い。

12. `app/domain/model/money.py:9,13-19` — docstring「不変条件：0以上」と実装（`__post_init__` は `pass` で無検証）が矛盾。CLAUDE.mdの設計意図（`Money(int)` 直接生成で負値許容）とは整合するが、docstringの記述が誤解を招く。

13. pytest実行時、Jinja2 `TemplateResponse(name, {"request": request, ...})` という非推奨の呼び出し順序でDeprecationWarningが11件発生（全ルーターで共通パターン）。将来のStarletteバージョンで動作しなくなる可能性。

14. `app/presentation/web/dependencies.py`（`get_db`）— 参照系（GET）リクエストでも毎回 `session.commit()` を呼んでいる。読み取り専用処理での不要なコミットオーバーヘッド。

## 検証コマンドの実行結果

- `ruff check app tests`: 22 errors（19 fixable）
- `pytest tests -q`: 121 passed（アーキテクチャ層方向の import 違反は検出されず）

## 件数サマリ

| 深刻度 | 件数 |
|---|---|
| 重大 | 2 |
| 中 | 5 |
| 軽微 | 7 |
| 合計 | 14 |
