# MN-002: 金額入力に0以上のバリデーションがない

## 事象

- 再現手順: 月次画面の収入・現金・引出・固定費履歴・生活費のいずれかのフォームで金額に負の数を入力して保存する
- 期待結果: `docs/basic_design.md` 2.3.2/2.3.3/2.3.5 の要件どおり「金額は0以上」が拒否される
- 実際の結果: `Money.__post_init__`（`app/domain/model/money.py`）が無検証、各フォームにも `ge=0` 等の制約が無く、負値がそのままDBに保存される

## 原因

- `Money` はCLAUDE.mdの設計上、損益など負を持ちうる値を `Money(int)` で直接生成できる必要があるため、`Money`自体に0以上の検証は入れられない
- 入力フォーム（`app/presentation/web/routers/month_router.py` の各 `Form(...)`）にも下限制約が付いていなかった

## 方針

- ユーザー承認: 2026-08-27、バリデーションは入力層（`Form(..., ge=0)`）のみに実装する方針で承認
- Command/Usecase層での二重検証は行わない（フォーム経由が唯一の入力経路のため）

## 修正

- `app/presentation/web/routers/month_router.py`: 以下の金額系Formフィールドに `ge=0` を追加
  - `register_income`: `salary_gross`, `salary_net`, `bonus_gross`, `bonus_net`
  - `save_cash_balance`: `amount`
  - `save_withdrawal`: `amount`
  - `save_next_cash_balance`: `amount`
  - `add_fixed_item_history`: `amount`
  - `save_living_expense` / `update_living_expense`: `amount`
- `tests/integration/test_amount_validation.py` を新規作成し、収入登録で負の金額が422で弾かれusecaseが呼ばれないことを検証（他エンドポイントも同一のFastAPI `Form(ge=0)` 機構のため代表1件を回帰テストとした）

## 既知の制約（本修正のスコープ外）

- 検証エラー時、`docs/basic_design.md` が想定する「入力フォーム＋エラーメッセージ部分更新」ではなく、FastAPI標準の422応答になる。既存コードでも一部のバリデーションエラー（例: `register_card_statements`のカード不正時）は未捕捉で同様に汎用エラーとなっており、既存の一貫性の範囲内
- カード請求登録（`register_card_statements`）の金額は動的フォームのため対象外。MN-004で別途対応
- `Settings.max_variable_items` 等の上限件数はMN-003で対応

## ミニ検証

- `ruff check app/presentation/web/routers/month_router.py tests/integration/test_amount_validation.py`: All checks passed
- `pytest tests -q`: 124 passed（修正前123 + 新規1件、既存テストの回帰なし）
- 画面確認: なし（バリデーション追加のみ、正常系の表示に変更なし）

## 影響範囲

- `app/presentation/web/routers/month_router.py`
- `tests/integration/test_amount_validation.py`
