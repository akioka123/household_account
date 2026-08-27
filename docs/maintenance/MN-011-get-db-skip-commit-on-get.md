# MN-011: get_dbがGETリクエストでも毎回commitしている

## 事象

- 再現手順: `app/presentation/web/dependencies.py` の `get_db` を確認する
- 期待結果: 更新系（POST等）リクエストのみcommitする
- 実際の結果: GET（参照系）リクエストでも毎回 `session.commit()` を呼んでいた。読み取り専用処理での不要なコミットオーバーヘッドになっていた

## 原因

- `get_db` がHTTPメソッドを見ずに、例外が出なければ常に `commit()` する実装になっていた

## 方針

- ユーザー承認: 2026-08-27（軽微項目の一括対応として）
- `get_db` に `Request` を注入し、`GET`/`HEAD`/`OPTIONS`（参照系）は `commit()` をスキップする
- 事前確認: 全ルーターの `@router.get` ハンドラを機械的に走査し、`.save(`/`.add_`/`.update_`/`.delete(`/`.execute(command` 等の書き込み系呼び出しが無いことを確認済み（本アプリのGETハンドラは参照専用）。GETでの書き込みが無い前提のため、commitスキップは安全

## 修正

- `app/presentation/web/dependencies.py`: `get_db(request: Request)` にシグネチャ変更し、`request.method not in {"GET", "HEAD", "OPTIONS"}` の場合のみ `commit()` する

## ミニ検証

- `ruff check app/presentation/web/dependencies.py`: All checks passed
- `pytest tests -q`: 128 passed（既存テストの回帰なし）
- **既知の制約**: 単体テストはモック、結合テストは `dependency_overrides` でユースケースを差し替えており、いずれも実DBを使わず `get_db` を経由しない。そのため本修正は実DB接続下での動作確認はしておらず、コードレビューと「GETハンドラに書き込みが無い」ことの静的確認のみで検証している。Docker環境（`docker compose up -d`）での動作確認を推奨

## 影響範囲

- `app/presentation/web/dependencies.py`
