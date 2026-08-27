# MN-001: 固定費のカード別集計が改定履歴を二重集計する

## 事象

- 再現手順: 同一固定費項目（fixed_item_id）に対し、カード紐づけ・カード含有ありの改定履歴を複数登録する（例: 2024-04 から5000円、2025-04 から6000円に改定）。改定後の月次サマリを表示する。
- 期待結果: カード変動費計算に使う「カードに含まれる固定費」は最新の履歴（6000円）のみで計算される
- 実際の結果: `FixedExpenses.by_card()` が改定前後の両方（5000円+6000円=11000円）を合計してしまい、CLAUDE.md定義の「カード変動費＝カード請求総額－カードに含まれる固定費」が過大な控除により狂う

## 原因

- `app/domain/model/fixed_expenses.py` の `calculate()` は `get_effective_histories()`（項目ごとに最新の履歴のみを残す）を使って正しく集計していたが、`by_card()` は `self.histories`（生の全履歴）をそのまま合計しており、`get_effective_histories()` を通していなかった
- `calculate()` 内では未使用の `fixed_in_card_by_card` を計算するデッドコードも残っていた（`by_card()` と同じ集計を二重に書いていた名残）
- `app/application/usecase/get_month_summary.py` と `app/infrastructure/persistence/repositories/sqlalchemy_month_summary_repository.py` の両方で `by_card()` を呼んでおり、月次画面・年次ダッシュボード双方に波及

## 方針

- ユーザー承認: 2026-08-27、`docs/review-current-implementation.md` の重大#1/中#3/中#7 をまとめて修正する方針で承認
- `calculate()` と `by_card()` が共通で使う `_latest_active_histories()`（`get_effective_histories()` → 削除済み除外）を切り出し、両メソッドをこれに統一
- 月次集計ロジックの重複解消（中#3）も同時に対応: `SqlAlchemyMonthSummaryRepository._calculate_summary` の独自集計を削除し、`GetMonthSummaryUseCase.execute()` に委譲するよう変更（CLAUDE.mdの層分離規約上、集計はapplication/usecaseに一本化）

## 修正

- `app/domain/model/fixed_expenses.py`: `by_card()` が `_latest_active_histories()`（内部で `get_effective_histories()` を使用）を参照するよう修正。`calculate()` のデッドコードを削除
- `app/infrastructure/persistence/repositories/sqlalchemy_month_summary_repository.py`: `_calculate_summary()` を `GetMonthSummaryUseCase` への委譲に置き換え。未使用importの `MonthSummaryRepository` も削除（ついでにruff指摘を解消）
- `tests/unit/domain/test_fixed_expenses.py`: 再発防止テストを追加
  - UT-FE-06: 改定履歴が複数あっても最新の1件のみをカード別集計に使う
  - UT-FE-07: 金額0（運用終了）の履歴はカード別集計からも除外される

## ミニ検証

- `ruff check app/infrastructure/persistence/repositories/sqlalchemy_month_summary_repository.py app/domain/model/fixed_expenses.py`: All checks passed
- `pytest tests -q`: 123 passed（修正前121 + 新規2件、既存テストの回帰なし）
- 画面確認: なし（バックエンド集計ロジックのみ、UIに新規要素はないため）

## 影響範囲

- `app/domain/model/fixed_expenses.py`（domain）
- `app/infrastructure/persistence/repositories/sqlalchemy_month_summary_repository.py`（infrastructure）
- `tests/unit/domain/test_fixed_expenses.py`

## トレーサビリティ

- UT-FE-06, UT-FE-07 を追加（既存 UT-FE-01〜05 の続番）
