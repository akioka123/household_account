# ゲート6 検証結果: 単体テスト（レシート金額抽出・生活費入力の詳細化）

- 検証者: verifier-test（第3層・検証系）
- 検証日: 2026-08-27
- 使用venv: `C:\projects\household_account\venv\Scripts\python.exe`（このworktreeにvenvが存在しないため、メインリポジトリのvenvを使用。builder-testの報告と同様の対応）
- 対応チェックリスト: `docs/gates/gate-6-checklist.md`
- 対応作業指示書: `docs/work-orders/6-unit-test-order.md`

## 総合判定: 合格（PASS）

## 実行ログ要約

| コマンド | 結果 |
|---|---|
| `pytest tests/unit -q` | **148 passed** in 0.76s（builder-test報告の148件と一致） |
| `pytest tests -q`（全体） | **159 passed**, 11 warnings in 6.92s（既存結合テスト含め回帰なし） |
| `ruff check app tests` | 22 errors（すべて既存ファイルの既知エラー。新規4ファイルには0件） |
| カバレッジ（新規4モジュール対象、`--cov-report=term-missing`） | TOTAL 271 stmts, miss 4, **99%**（80%基準を達成） |

カバレッジ内訳:

| モジュール | Stmts | Miss | Cover |
|---|---|---|---|
| `app/application/usecase/manage_living_expense_items.py` | 158 | 3 | 98% |
| `app/domain/model/living_expense_item.py` | 26 | 0 | 100% |
| `app/domain/service/receipt_paste_parser.py` | 50 | 0 | 100% |
| `app/infrastructure/storage/filesystem_receipt_image_storage.py` | 37 | 1 | 97% |

## ゲート6チェックリスト 10項目の判定

| # | チェック項目 | 判定 | 根拠 |
|---|---|---|---|
| 1 | work-order 2-1〜2-4の全観点に対応するテストケースが存在する | PASS | 4ファイルを実読し、2-1（正常系・負値例外・不正小分類例外）、2-2（判定規則1〜5＋複数行正常系＋混在エラー）、2-3（レシート作成2種・追加/編集/削除の再計算・get_receipts絞り込み・小分類集計・プレビュー・一括保存All-or-Nothing・レシート削除カスケード）、2-4（PNG/JPEG保存・不正データ/空データ拒否・delete正常/対象なし）を1件ずつ突合、漏れなし |
| 2 | 4.4.4節の親`amount`再計算（追加・編集・削除）がテストされている | PASS | `test_add_item_recalculates_parent_amount`（0→200）、`test_update_item_recalculates_parent_amount`（200→800、他品目300+編集後500の合計を実値検証）、`test_delete_item_recalculates_parent_amount_to_remaining_sum`（500→300）、`test_delete_item_recalculates_to_zero_when_no_items_remain`（300→0）といずれも`save.call_args`から実際の`amount.amount`を取り出し数値を検証しており、「呼ばれたか」だけでなく計算結果そのものを検証している。モック`find_by_living_expense_id`の`side_effect`が実装の呼び出し回数・順序（採番用1回目→再計算用2回目）と整合していることも実装コードと突合し確認済み |
| 3 | `get_receipts()`の絞り込み条件（`category="food"`かつ`location=""`、品目0件を含む）がテストされている | PASS | `test_get_receipts_filters_food_category_with_empty_location_only`が「レシート由来（food/location=""）」「簡易入力食費（food/location="スーパー"）」「食費以外（electricity/location=""）」の3件を用意し、結果が1件（id=1のみ）であることを検証。ゲート5の重大指摘（`location`条件漏れ）の再発防止として機能している。`test_get_receipts_includes_receipts_with_zero_items`で品目0件でも一覧に含まれることも別途検証 |
| 4 | 貼り付け一括保存のAll-or-Nothing挙動がテストされている | PASS | `test_save_paste_saves_all_when_all_lines_valid`（全行正常→2件保存、親amount=500）と`test_save_paste_saves_nothing_when_any_line_invalid`（1行不正→`item_repo.save`/`living_expense_repo.save`とも`assert_not_called()`）の両方向を検証 |
| 5 | TSVパーサの判定規則5つすべてに対応するテストケースがある | PASS | 規則1（空行無視）、規則2（3項目不一致・過剰列）、規則3（非数値・負数・0円境界値）、規則4（未知ラベル）、規則5（空文字・空白のみ）を個別テストケースで網羅。加えて複数行正常系・エラー混在時の他行非影響も検証 |
| 6 | Portのモックが`MagicMock(spec=<Port>)`パターンで既存規約に従っている | PASS | `test_manage_living_expense_items.py`のfixtureで`MagicMock(spec=LivingExpenseRepository)`等＋`AsyncMock`を使用し既存規約と一致。domain層テストと`test_filesystem_receipt_image_storage.py`（`tmp_path`で実ファイルシステムを使用、work-order 2-4の指定通り）はモック不要のため対象外 |
| 7 | `pytest tests/unit -q`が全件成功する | PASS | 148 passed |
| 8 | `pytest tests -q`（全体）で既存テストの回帰がない | PASS | 159 passed（結合テスト含む） |
| 9 | `ruff check app tests`がエラーなし | PASS | 新規4ファイルは0件（既存22件は対象外の既知エラーで一致） |
| 10 | Repository実装・router（結合テスト範囲）に対する単体テストが誤って作成されていない | PASS | `git status --porcelain tests/`で新規ファイルが指定の4件のみであることを確認 |

## テストの実効性確認（不具合を覆い隠す書き方になっていないか）

- 親amount再計算テストは`Money.amount`の実数値をassertしており、モックが常にTrueを返すだけの空検証ではない
- `get_receipts()`絞り込みテストは「除外されるべきデータ」を意図的に混在させ、結果件数・IDで除外を確認しており、フィルタ条件が緩んでいても検出できる構造になっている
- `test_filesystem_receipt_image_storage.py`はモックを使わず、Pillowで実際にエンコードしたPNG/JPEGバイト列を実ファイルシステム（`tmp_path`）に対して保存・検証しており、実装の不具合をそのまま検出できる
- 各テストの実装コード（`manage_living_expense_items.py`, `living_expense_item.py`, `filesystem_receipt_image_storage.py`）を読み、モックの`side_effect`/`return_value`が実装の実際の呼び出し回数・順序と整合していることを確認済み（過剰スタブによる検証の空洞化なし）

## 結論

新規4テストファイル（`tests/unit/domain/test_living_expense_item.py`, `tests/unit/domain/test_receipt_paste_parser.py`, `tests/unit/application/test_manage_living_expense_items.py`, `tests/unit/infrastructure/test_filesystem_receipt_image_storage.py`）はゲート6チェックリスト10項目すべてを満たし、合格と判定する。差し戻し事項なし。
