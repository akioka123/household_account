# MN-004: カード請求0円入力がサイレントに無視される

## 事象

- 再現手順: 月次画面の変動費タブで、既存のカード請求額を0円に訂正して保存する
- 期待結果: 請求額が0円で保存される（請求なし、の意味として）
- 実際の結果: `register_card_statements`（`app/presentation/web/routers/month_router.py`）が `amount_val > 0` でフィルタしており、0円の行がそのまま無視され、既存の請求額が残り続ける。エラー表示も無く、ユーザーは訂正が反映されなかったことに気づけない

## 原因

- フォームデータからカード請求コマンドを組み立てる箇所で `amount_val > 0` としており、0円を無効な入力と同じ扱いにしていた

## 方針

- ユーザー承認: 2026-08-27、0円も保存可能にする方針で承認（既存請求を0円に訂正する手段を提供するため）
- 負の金額は従来どおり除外する（このフォームは動的行のためMN-002のFastAPI `Form(ge=0)` の対象外。`amount_val >= 0` とすることで0円のみ許可し、負値は引き続き弾かれる）

## 修正

- `app/presentation/web/routers/month_router.py`: `register_card_statements` 内のフィルタ条件を `amount_val > 0` → `amount_val >= 0` に変更
- `tests/integration/test_register_card_statements_endpoint.py` を新規作成
  - 0円行がusecaseに渡されることを検証
  - 負の金額行は従来どおり除外されることを検証（回帰防止）

## ミニ検証

- `ruff check app/presentation/web/routers/month_router.py tests/integration/test_register_card_statements_endpoint.py`: All checks passed
- `pytest tests -q`: 128 passed（修正前126 + 新規2件、既存テストの回帰なし）
- 画面確認: なし（フィルタ条件の1文字変更のみ、既存表示に影響なし）

## 影響範囲

- `app/presentation/web/routers/month_router.py`
- `tests/integration/test_register_card_statements_endpoint.py`
