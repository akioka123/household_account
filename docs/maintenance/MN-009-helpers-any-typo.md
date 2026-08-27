# MN-009: helpers.pyの型ヒント`any`が組み込み関数を指している

## 事象

- 再現手順: `app/presentation/web/helpers.py:6` の `get_years_with_data` の戻り値型ヒントを確認する
- 期待結果: `list[dict[str, Any]]`（`typing.Any`）
- 実際の結果: `list[dict[str, any]]` と小文字になっており、`typing.Any` ではなく組み込み関数 `any` を指していた（型チェッカー上は意味を成さない）

## 原因

- `typing.Any` の書き間違い（`from typing import Any` も無かった）

## 方針

- ユーザー承認: 2026-08-27（軽微項目の一括対応として）

## 修正

- `app/presentation/web/helpers.py`: `from typing import Any` を追加し、戻り値型ヒントを `list[dict[str, Any]]` に修正
- ついでに、関数シグネチャがCLAUDE.mdの規約（line-length 100）を超えていたため複数行に整形（既存の内容の踏襲、挙動変更なし）

## ミニ検証

- `ruff check app/presentation/web/helpers.py`: All checks passed
- `pytest tests -q`: 128 passed（既存テストの回帰なし）
- 画面確認: なし（型ヒントのみの修正、実行時の挙動に変化なし）

## 影響範囲

- `app/presentation/web/helpers.py`
