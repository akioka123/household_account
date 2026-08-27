# 作業指示書: ゲート6（単体テスト）— レシート金額抽出・生活費入力の詳細化

- 宛先: builder-test
- 工程: unit-test（ゲート6）
- 発行: 統括（トークン節約モードによりpm役を代行）
- 対象: ゲート5で実装した以下のモジュールに対する `tests/unit/` 配下の単体テスト作成

## 1. 読むべき入力

1. `docs/03-basic-design.md`（4章モジュール設計、4.1.3節TSVパーサ判定規則、4.4.4節親レシート整合ルール）
2. `docs/01-user-stories.md`（US-01〜04の受け入れ基準。テストケースの根拠にする）
3. 実装本体: `app/domain/model/living_expense_item.py`, `app/domain/service/receipt_paste_parser.py`, `app/application/usecase/manage_living_expense_items.py`, `app/infrastructure/storage/filesystem_receipt_image_storage.py`
4. 既存の単体テスト（作法の踏襲）: `tests/unit/` 配下の既存 `test_manage_living_expenses.py` 等、Portを `MagicMock(spec=<Port>)` + `AsyncMock` で差し替えるパターン
5. プロジェクト `CLAUDE.md`（`asyncio_mode = auto` のため `@pytest.mark.asyncio` は任意）

## 2. テスト対象と観点

### 2-1. `app/domain/model/living_expense_item.py`（`LivingExpenseItem`）

- 正常系: 有効な値でインスタンス化できる
- 不変条件: 金額が負の場合に `__post_init__` で例外になること（`Money`の制約を使っているか、独自検証かは実装を確認して合わせる）
- 小分類が `LIVING_EXPENSE_ITEM_SUBCATEGORIES` に含まれない値の場合の扱い（実装が検証しているならそれをテストする。検証していないなら無理にテストを追加しない＝実装の実態に合わせる）

### 2-2. `app/domain/service/receipt_paste_parser.py`（`parse_receipt_paste_text`）

基本設計4.1.3節の判定規則5つを1つずつテストする（各規則ごとに最低1テストケース）。
1. 空行は無視される
2. タブで3項目に一致しない行はエラー
3. 金額が非負整数として解析できない行はエラー
4. 小分類が固定リストのラベル（食品/生活用品）に一致しない行はエラー
5. 品目名が空文字の行はエラー
6. 加えて: 複数行の正常系（3行程度、食品・生活用品混在）が正しくパースされること
7. 正常行とエラー行が混在する入力で、正常行は正しく解析されエラー行のみエラーになること（1行のエラーが他行に影響しないこと）

### 2-3. `app/application/usecase/manage_living_expense_items.py`（`ManageLivingExpenseItemsUseCase`）

Portを `MagicMock(spec=LivingExpenseItemRepository)` / `MagicMock(spec=ReceiptImageStoragePort)` 等でモックして検証する。

- レシート作成（画像なし）: `LivingExpense`が`category="food"`, `location=""`, `amount=0`で作成されること
- レシート作成（画像あり）: `ReceiptImageStoragePort.validate_and_save`が呼ばれ、成功時は`receipt_image_path`が設定されること／検証失敗時（`ValueError`等）はレシートを作成せずエラーが伝播すること
- 品目追加: 追加後、親`LivingExpense.amount`が品目合計に再計算されて保存されること（4.4.4節。**最重要テストケース**）
- 品目編集: 編集後も親`amount`が再計算されること
- 品目削除: 削除後も親`amount`が再計算されること（残り品目の合計になること。0件になった場合は`amount=0`になること）
- `get_receipts()`: `category="food"` かつ `location=""` の`LivingExpense`のみを対象とすること。品目0件のレシート（作成直後）も含まれること。通常の簡易入力食費（`location`あり）は含まれないこと（**ゲート5で修正した重要な条件のため必ずテストする**）
- 小分類別集計: 登録0件の小分類も0円として結果に含まれること（除外されないこと）
- 貼り付けプレビュー: 保存を行わず、解析結果（正常行・エラー行）を返すこと
- 貼り付け一括保存: 全行正常なら一括保存されること／1行でも不正なら1件も保存されないこと（All-or-Nothing、US-03 AC5）
- レシート削除: 品目も含めてカスケード削除されること、画像ファイルがある場合は`ReceiptImageStoragePort.delete`が呼ばれること

### 2-4. `app/infrastructure/storage/filesystem_receipt_image_storage.py`（`FilesystemReceiptImageStorage`）

`tmp_path`（pytest標準フィクスチャ）を使い、実際のファイルシステムに対してテストする（DBを使わないためこれは単体テストの範囲内）。

- 正常な画像データ（有効なPNG/JPEGバイト列）を保存すると、相対パスが返り、実際にファイルが作成されること
- 不正なデータ（画像として読めないバイト列）を渡すと`ValueError`等の例外になり、ファイルが保存されないこと
- `delete()`で保存したファイルが削除されること

## 3. 実施しないこと

- `app/infrastructure/persistence/repositories/sqlalchemy_living_expense_item_repository.py`（Repository実装）・`month_router.py`のテストは対象外（結合テストがDBなし・ユースケースモックで担当する範囲であり、プロジェクトの既存慣習どおり単体テストでは扱わない）
- 既存の生活費機能（`ManageLivingExpensesUseCase`等）に対する新規テスト追加は不要（無変更のため）

## 4. 完了条件

- `tests/unit/` 配下に新規テストファイルを作成し、`./venv/Scripts/python.exe -m pytest tests/unit -q` を実行してすべて成功することを確認する
- `./venv/Scripts/python.exe -m ruff check app tests` でテストコードにlintエラーがないことを確認する
- 完了したら統括に、作成したテストファイル一覧・テストケース数・実行結果を報告する
