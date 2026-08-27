# MN-008: Jinja2Templatesの毎回生成、および非推奨の呼び出し順序

## 事象

- 再現手順: `pytest tests -q` を実行する
- 期待結果: DeprecationWarningが出ない
- 実際の結果:
  - `dashboard_router.py` / `month_router.py` / `settings_router.py` / `fixed_items_router.py` の各ハンドラがリクエスト毎に `Jinja2Templates(directory=...)` を再生成していた（レビュー軽微#10）
  - `templates.TemplateResponse(name, {"request": request, ...})` という非推奨の呼び出し順序でDeprecationWarningが11件発生していた（レビュー軽微#13）

## 原因

- ハンドラごとに `from fastapi.templating import Jinja2Templates` と `Jinja2Templates(directory=...)` をコピペしており、モジュールレベルへの共通化が漏れていた
- Starlette側でTemplateResponseの引数順序（`request`を第1引数にする新形式）への移行が進んでいたが、旧形式（`name`を第1引数にしてcontext dictに`"request"`キーを含める）のまま放置されていた

## 方針

- ユーザー承認: 2026-08-27（軽微項目の一括対応として）
- `templates = Jinja2Templates(...)` を各ファイルのモジュールレベルに1回だけ定義し、ハンドラ内の再生成を削除
- 全 `TemplateResponse(...)` 呼び出しの第1引数に `request` を追加（新形式）。context dict内の `"request": request` は`Jinja2Templates.TemplateResponse`が`context.setdefault("request", request)`で吸収するため無害。残しても実害がなく、削除すると `_summary_tab_context` 等のヘルパー関数側の戻り値構造まで触る必要が出るため、今回は呼び出し側の引数順序修正のみに限定し、context dictの中身には手を入れない

## 修正

- `app/presentation/web/routers/month_router.py`（23箇所）, `dashboard_router.py`（2箇所）, `settings_router.py`（5箇所）, `fixed_items_router.py`（1箇所）
  - モジュールレベルで `templates = Jinja2Templates(directory="app/presentation/templates")` を1回定義
  - 各ハンドラ内の重複したインポート・再生成コードを削除
  - `TemplateResponse(...)` 呼び出しの第1引数に `request` を追加（計31箇所）

## ミニ検証

- `ruff check`（変更4ファイル）: All checks passed
- `pytest tests -q`: 128 passed（既存テストの回帰なし）
- `pytest tests -q -W error::DeprecationWarning`: 128 passed（DeprecationWarningが1件も発生しないことを確認）
- 画面確認: なし（レスポンス内容は不変、生成方法とAPI呼び出し形式のみの変更）

## 影響範囲

- `app/presentation/web/routers/month_router.py`
- `app/presentation/web/routers/dashboard_router.py`
- `app/presentation/web/routers/settings_router.py`
- `app/presentation/web/routers/fixed_items_router.py`
