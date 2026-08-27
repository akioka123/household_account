# 検証記録: レシート金額抽出・生活費入力の詳細化（実装／ゲート5）

- 検証者: verifier-code（構築系エージェント builder-impl とは独立）
- 検証対象: MOD-01〜12実装一式、`alembic/versions/010_create_living_expense_items.py`、`requirements.txt`、`.gitignore`
- 検証基準: `docs/gates/gate-5-checklist.md`（13項目）、`docs/work-orders/5-impl-order.md`、`docs/03-basic-design.md`（2章・3章・4章・ADR-001）、プロジェクト `CLAUDE.md`
- 検証日: 2026-08-25（初回）／2026-08-25（再検証・本記録の最新セクション）
- 実行環境: `C:\projects\household_account\venv\Scripts\python.exe`（worktree専用venvが存在しないため、メインチェックアウトのvenvインタプリタでworktree配下のapp/testsを対象に実行）

## 総合判定（再検証）: 合格

前回検証で指摘したCritical指摘1件は解消を確認した。Low指摘2件のうち指摘3（フォームリスト長不一致の防御）も対応済み。指摘2（リポジトリ全体のruff）は前回どおり本機能起因ではないことを再確認した。gate-5-checklist 13項目すべてPASS。

---

## 再検証（差分確認）2026-08-25

### 確認1: `get_receipts()` の修正（指摘1 Critical の解消確認）

- **該当箇所**: `app/application/usecase/manage_living_expense_items.py` 268-288行目
- **修正内容**: 条件を「品目1件以上」から「`category == LIVING_EXPENSE_CATEGORY_FOOD` かつ `location == ""`」に変更。品目0件のレシートも一覧（`ReceiptSummary`）に含まれるようになった。
- **区別の妥当性**: `app/application/usecase/manage_living_expenses.py` 94行目・136行目で、簡易入力側は食費カテゴリの場合 `location` が空文字だとバリデーションエラーになる（`add_living_expense`/`update_living_expense`）ことをコードで確認した。したがって簡易入力の食費エントリの `location` が空文字になることはなく、`location == ""` はレシート経由（`ManageLivingExpenseItemsUseCase._save_new_receipt` / `create_receipt_with_image`、いずれも `location=""` で生成）の行とのみ一致する。**両者の混同は発生しない。**
- **フェイクリポジトリによる再現確認**: 実プロダクトコードの `ManageLivingExpenseItemsUseCase` をそのままインポートし、以下のシナリオをDBなしで実行した。
  1. 簡易入力の食費（`location="スーパーA"`）を1件事前登録
  2. `create_receipt()` でレシート（品目0件）を作成
  3. `get_receipts()` を呼び出し

  ```
  作成されたレシート: LivingExpense(id=101, ..., location='', amount=Money(amount=0), ...)
  get_receipts() の結果件数: 1
    id=101, item_count=0, location=''
  作成直後のレシート(id=101)が一覧に含まれるか: True
  簡易入力の食費(id=100)が誤って混入していないか(混入していなければFalse): False
  品目追加後の件数: 1
  ```

  品目0件のレシートが一覧に含まれること、簡易入力の食費が誤って混入しないことの両方を実証した。
- **テンプレート側の到達経路**: `living_tab.html` 177-244行目を確認。`get_receipts()` の結果に品目0件のレシートが含まれるようになったことで、`{% for receipt in receipts %}` ループ内に当該レシートの `<details>` パネルが出力され、`active_receipt_id` による自動展開（179行目）と `receipt_item_form.html` の埋め込み（243行目）が機能する。品目0件時は「品目は登録されていません。」（239行目）が表示され、直下に品目追加フォームが出力されることを確認した。**US-01・US-02のハッピーパスがUIから到達可能になった。**
- **副次的な問題の解消**: 前回指摘した「品目0件のレシートが簡易入力の食費一覧に空欄行として紛れ込む」問題も、同じ `get_receipts()` の結果を使う除外ロジック（`month_router.py` 1062-1069行目 `receipt_ids`）が品目0件のレシートIDも含むようになったことで解消されていることを確認した（副作用として解消、報告にはないが実装上妥当）。
- **判定**: 修正は妥当。**指摘1（Critical）は解消。**

#### 参考: 基本設計3.3節の記述との差分（ブロッキングではない指摘）

`docs/03-basic-design.md` 3.3節（116-117行目）は、レシート一覧の対象・簡易入力からの除外条件をいずれも「品目1件以上を持つ `LivingExpense`」と文言で定義している。これは3.2節（状態遷移: 品目0件でもSCR-03へ遷移）と矛盾しており、前回のCritical指摘はこの3.2/3.3間の設計内矛盾に起因していた。今回の修正は3.2節の要求を優先し、`location==""` を基準とすることで矛盾を解消しているが、3.3節の文言（「品目1件以上を持つ」）自体は更新されていない。コードの挙動は3.2節の要求・機能要件を正しく満たしており是正不要だが、基本設計3.3節の記述を実装に合わせて更新することが望ましい。**重要度: 低（Info相当）。ドキュメント整合性の課題であり、機能・Must要件には影響しない。builder-docsまたは基本設計の次回改訂時の対応を推奨。**

### 確認2: `save_receipt_paste` のガード追加（指摘3 Low の解消確認）

- **該当箇所**: `app/presentation/web/routers/month_router.py` 1495-1514行目
- **修正内容**: `form_data.getlist("name")` / `"amount"` / `"sub_category"` の3リストの長さが一致しない場合、`zip()` による暗黙の行欠落を避けて保存せずにエラーメッセージ（「送信されたデータの形式が不正です。もう一度貼り付けからやり直してください」）を表示して早期リターンする。
- **既存パターンとの整合**: `error_message` / `active_receipt_id` を使ったエラー表示は同ファイル内の他ハンドラ（1158, 1199, 1363, 1409行目）と同じパターンで実装されており、命名・戻り値（`_living_tab_full_context` 経由の `TemplateResponse`）とも一致する。
- **セキュリティ**: エラーメッセージは静的文字列であり、ユーザー入力を直接埋め込んでいないためXSSリスクなし（Jinja2の自動エスケープにも依存しない安全な実装）。
- **判定**: 修正は妥当。**指摘3（Low）は解消。**

### 確認3: `ruff check app tests`

```
./venv/Scripts/python.exe -m ruff check app tests   # リポジトリ全体: 22エラー（前回と同数・同一箇所、本機能に起因しない既存エラー）
./venv/Scripts/python.exe -m ruff check <manage_living_expense_items.py> <month_router.py>
  → All checks passed!
```

修正対象の2ファイルはエラー0件。リポジトリ全体の22件は前回検証時と同一（`test_manage_fixed_items.py`、`test_income.py`、`test_structured_logger.py`等の既存テストファイルのF401/F841であり、本機能の差分外）。**指摘2の内容に変化なし（Low・是正不要のまま）。**

### 確認4: 回帰確認

- `pytest tests -q`（worktree配下、メインvenv実行）: **121 passed**、失敗・エラーなし。既存の単体・結合テストに新たな不整合は生じていない。
- `docs/gates/gate-5-checklist.md` 13項目を再走査し、今回の修正差分（`get_receipts()`、`save_receipt_paste`）が他項目（DI規約・命名規則・Won't要件・日本語docstring等）に抵触しないことを確認した。新規ファイルは追加されておらず項目1（パス・命名）への影響なし。追加されたコメント・エラーメッセージはすべて日本語で曖昧語なし（項目12）。`tests/`配下に新規ファイルなし（項目13、`git status`で再確認済み）。

## チェックリスト項目別確認結果（`docs/gates/gate-5-checklist.md`）再掲・更新

| # | チェック項目 | 判定 | 根拠 |
|---|---|---|---|
| 1 | MOD-01〜12が基本設計どおりのパス・命名で存在する | PASS | 今回の修正は既存2ファイルの差分のみ、新規ファイルなし |
| 2〜9 | （前回検証から変更なし） | PASS | 前回検証時と同一（`get_receipts()`/`save_receipt_paste`以外は無変更） |
| 10 | Won't(US-05〜11)に反する実装がない | PASS | 修正差分に外部API・レスポンシブCSS・自動バックアップ・品目名一覧表示なし |
| 11 | `ruff check app tests`がエラーなしで通る | 条件付きPASS | 変更2ファイルはエラー0件。リポジトリ全体の既存22件は前回同様、本機能外 |
| 12 | docstring・コメント・UI文言が日本語、曖昧語なし | PASS | 追加分（`get_receipts()`docstring、ガードのコメント・エラーメッセージ）を確認 |
| 13 | テストコードが本工程で新規作成されていない | PASS | `git status`で`tests/`配下に新規ファイルなしを再確認 |

## 指摘件数（再検証後）

- 重大（Critical）: 0件（前回指摘1は解消済み）
- 軽微（Low）: 1件（指摘2、内容不変・是正不要）
- 参考（Info）: 1件（基本設計3.3節の文言更新推奨、機能へは無影響）
- 総合判定: **合格**

## 差し戻し事項

なし。ゲート5合格として次工程（ゲート6・単体テスト）へ進めてよい。基本設計3.3節の文言更新（Info指摘）は任意対応とし、必要であれば別途ドキュメント修正のタスクとして扱う。
