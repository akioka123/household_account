# MN-007: 月次ルーターの重複DB呼び出し・変数二重代入

## 事象

- 再現手順: `app/presentation/web/routers/month_router.py` の `fixed_tab` / `add_fixed_item` / `add_fixed_item_history` を読む
- 期待結果: 各データ取得・変数代入は1回のみ
- 実際の結果: コピペ起因で以下が重複していた
  - `fixed_tab`: `get_active_fixed_items_at` / `get_all_fixed_items` / `get_all_cards` を含むブロック全体が2回（無効な最初のブロックの結果は使われず、無駄なDB呼び出しになっていた）
  - `add_fixed_item`: `get_active_fixed_items_at` が2回
  - `add_fixed_item_history`: `get_active_fixed_items_at` が2回、`card_id_int: int | None = None` の代入が2回

## 原因

- ハンドラ実装時のコピペで、同じ取得処理を消し忘れたまま残していた（`end_fixed_item_operation` は同じ処理を単一呼び出しで正しく実装しており、他の3箇所だけが重複していた）

## 方針

- ユーザー承認: 2026-08-27（軽微項目の一括対応として）
- 重複行・重複ブロックを削除し、`end_fixed_item_operation` と同じ単一呼び出しの形に揃える

## 修正

- `app/presentation/web/routers/month_router.py`
  - `fixed_tab`: 重複していた取得ブロックを1つに統合（コメント付きの版を残す）
  - `add_fixed_item`: `get_active_fixed_items_at` の重複呼び出しを削除
  - `add_fixed_item_history`: `get_active_fixed_items_at` の重複呼び出しと `card_id_int` の重複代入を削除

## ミニ検証

- `ruff check app/presentation/web/routers/month_router.py`: All checks passed
- `pytest tests -q`: 128 passed（既存テストの回帰なし。挙動は変えず、無駄な呼び出しを削っただけのため新規テストは追加していない）
- 画面確認: なし（返却データは変更前後で同一）

## 影響範囲

- `app/presentation/web/routers/month_router.py`
