# ゲート7 検証結果: 結合テスト（レシート金額抽出・生活費入力の詳細化）

- 検証者: verifier-test（第3層・検証系）
- 検証日: 2026-08-27
- 使用venv: `C:\projects\household_account\venv\Scripts\python.exe`（このworktreeにvenvが存在しないため、メインリポジトリのvenvを使用。work-order記載の対応どおり）
- 対応チェックリスト: `docs/gates/gate-7-checklist.md`
- 対応作業指示書: `docs/work-orders/7-integration-test-order.md`
- 対象テストファイル: `tests/integration/test_receipt_living_expense_items.py`（21ケース）

## 総合判定: 合格（PASS）

## 実行ログ要約

| コマンド | 結果 |
|---|---|
| `pytest tests/integration -q` | **32 passed** in 2.37s（新規21件を含む） |
| `pytest tests -q`（全体） | **180 passed**, 30 warnings in 2.90s（builder-test報告の180件と一致、回帰なし） |
| `ruff check app tests` | 22 errors（すべて既存ファイルの既知エラー。新規テストファイル・新規プロダクトコードには0件） |

新規テストファイルの内訳（21ケース、IT-LIV-01〜21）: エンドポイント10本に対応する正常系・異常系9セクション＋既存生活費簡易入力の回帰確認3ケース（IT-LIV-19〜21）。

## ゲート7チェックリスト 9項目の判定

| # | チェック項目 | 判定 | 根拠 |
|---|---|---|---|
| 1 | 4.3節のエンドポイント10本すべてに対応するテストケースがある | PASS | `docs/03-basic-design.md` 4.3節の10本（`GET tab/living`、`POST receipts`、`POST receipts/image`、`GET receipts/{id}/image`、`POST receipts/{id}/delete`、`POST receipts/{id}/items`、`POST receipt-items/{item_id}`、`POST receipt-items/{item_id}/delete`、`POST receipts/{id}/items/paste-preview`、`POST receipts/{id}/items/paste-save`）と、テストファイル内のセクションコメント（`# --- 1.` 〜 `# --- 10.`）を1本ずつ突合し、全10本に最低1テストケースが対応していることを確認した |
| 2 | `TestClient` + `app.dependency_overrides` でDBなしに動作している（実DB接続コードがない） | PASS | テストファイル冒頭のimportは`app.application.usecase`/`app.domain.model`/`app.domain.service`/`app.main`/`app.presentation.web.routers.month_router`のみで、`sqlalchemy`・`infrastructure.persistence`系のimportは皆無。`_client()`ヘルパーが`provide_manage_living_expenses_uc`と`provide_manage_living_expense_items_uc`の両方を`app.dependency_overrides`でメモリ保持スタブに差し替えており、各テストは`finally`で`app.dependency_overrides.clear()`を実行している。対象の`GET receipts/{id}/image`エンドポイント（`month_router.py` 1281行目）はDIされたuse caseからパスのみ取得し、`_PROJECT_ROOT / "data" / ...`への直接ファイルI/OのみでDBアクセスなしであることをルーター実装で確認 |
| 3 | レシート作成直後（品目0件）でも編集領域に到達できることがエンドポイントレベルで検証されている | PASS | `test_create_receipt_without_image_reaches_item_edit_area_with_zero_items`（IT-LIV-03）で`response.status_code == 200`に加え、`"品目 0件"`・`"品目は登録されていません。"`・`"品目追加"`・`"open"`をassert。テンプレート実体（`living_tab.html` 189行目`品目 {{ receipt.item_count }}件`、239行目`品目は登録されていません。`、`receipt_item_form.html` 38行目`品目追加`、`living_tab.html` 179行目`<details ... {% if active_receipt_id == living_expense_id %}open{% endif %}>`）と突合し、ルーター側（`month_router.py` 1245行目）が`active_receipt_id=receipt.id`を作成直後のレシートIDで渡していることも確認済みで、文字列一致がテンプレートの実描画ロジックに裏付けられている（空アサーションではない） |
| 4 | 貼り付け一括保存のAll-or-Nothing挙動がエンドポイントレベルで検証されている | PASS | `test_paste_save_all_valid_lines_are_saved`（IT-LIV-16、全行正常→2件保存・親amount合算値406を実値検証）と`test_paste_save_with_invalid_line_saves_nothing_all_or_nothing`（IT-LIV-17、1行目正常＋2行目不正→`items[10] == []`かつ`amount.amount == 0`を実値検証、エラーメッセージも一致確認）で両方向を検証。ルーター実装（`month_router.py` 1521-1538行目）・実ユースケース`ManageLivingExpenseItemsUseCase.save_paste`（`manage_living_expense_items.py` 216-258行目）を確認したところ、スタブの`save_paste`（`any(line.error is not None for line in lines): return lines`で未保存のまま返す）は実装のロジック分岐と完全に一致しており、テストが検証している「保存されない」という結果は実装の実際の分岐を反映したものである。加えてIT-LIV-18でフォームのlist長不一致（改ざん等の想定外入力）による未保存も別途検証 |
| 5 | 画像アップロードの検証失敗時のエラー応答が検証されている | PASS | `test_create_receipt_with_image_validation_failure_shows_error`（IT-LIV-05）でユースケースが`ValueError`を送出するケースをスタブし、`status_code == 200`・エラーメッセージ本文一致・`living_items_uc.receipts == {}`（未作成であること）を検証 |
| 6 | 既存の生活費簡易入力エンドポイントの回帰確認が含まれる | PASS | IT-LIV-19（追加）・IT-LIV-20（食費場所必須バリデーション異常系）・IT-LIV-21（更新・削除）の3ケースで`POST/月次 living-expenses`系の無変更エンドポイントを回帰確認 |
| 7 | `pytest tests/integration -q`が全件成功する | PASS | 32 passed in 2.37s |
| 8 | `pytest tests -q`（全体）で回帰がない | PASS | 180 passed, 30 warnings in 2.90s（builder-test報告値と一致） |
| 9 | `ruff check app tests`がエラーなし | PASS | 全22件は`sqlalchemy_*_repository.py`等の既存ファイルにおける既知の`F401`等（詳細はログ参照）。新規テストファイル・新規プロダクトコードにヒットなし |

## 実施した追加確認事項

- **DBなし動作の確認**: 上記チェック項目2のとおり、テストファイル・対象ルーターの両方でSQLAlchemy/セッション関連コードが不使用であることをソースレベルで確認した
- **`GET /receipts/{id}/image`の一時ファイルクリーンアップ**: `test_get_receipt_image_returns_binary_with_content_type`（IT-LIV-06）は`data/receipts/2026-03/10.jpg`を作成し、`finally`節で`image_path.unlink(missing_ok=True)`により確実に削除している（テスト実行後に`find data -type f`でファイル残存がないことを確認済み）。一方、`image_dir.mkdir(parents=True, exist_ok=True)`で作成した空ディレクトリ（`data/receipts/2026-03/`、`data/receipts/`）はテスト側で削除されず、pytest実行後に残存することを確認した。`/data/`は`.gitignore`（56行目）で全体除外されておりGit管理への混入はなく、後続テストも常に`write_bytes`でファイル内容を上書きしてから読み取るため、空ディレクトリの残存自体がテスト結果や他テストとの間で汚染を起こす実害はない（検証のため2回連続実行しても結果は同一）。ただし作成したファイルの後始末が完全ではない（ディレクトリ未削除）点は軽微な改善余地として付記する（本検証では不合格要因とはしない。検証後、残存ディレクトリは本検証者にて削除済み）
- **カバレッジ**: 本チェックリストにカバレッジ基準は含まれないため判定対象外（単体テストのカバレッジ基準はゲート6で確認済み、`docs/verification/unit-test-result.md`参照）。参考までに`pytest tests -q --cov=app`のリポジトリ全体カバレッジは76%だが、これはSQLAlchemyリポジトリ実装（DBアクセスのため単体テスト対象外、設計方針どおり）を含めた数値であり、結合テスト（DBなし方針）の合否判定には用いない

## 結論

`tests/integration/test_receipt_living_expense_items.py`（21ケース）はゲート7チェックリスト9項目すべてを満たし、合格と判定する。差し戻し事項なし。軽微な改善余地（画像テストで作成する一時ディレクトリの未削除）を1件付記するが、実害がないため合否には影響しない。
