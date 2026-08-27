# ゲート5 チェックリスト: 実装（レシート金額抽出・生活費入力の詳細化）

- 対象成果物: MOD-01〜MOD-12実装一式、マイグレーション、requirements.txt、.gitignore
- 対応する作業指示書: `docs/work-orders/5-impl-order.md`
- 使用スキル: `gate-check`（判定レポートは `docs/gates/gate-5-report.md` に作成）
- 判定方針: 1項目でもFAILなら総合不合格

| # | チェック項目 | 確認方法 |
|---|---|---|
| 1 | MOD-01〜MOD-12すべてのファイルが基本設計どおりのパス・命名で存在する | ファイル一覧を基本設計2章と突合 |
| 2 | `LivingExpenseItem`が`@dataclass(frozen=True)`で、金額0以上等の不変条件が`__post_init__`にある | 該当ファイルを確認 |
| 3 | Port(`LivingExpenseItemRepository`, `ReceiptImageStoragePort`)がProtocolで定義され、実装クラスが`SqlAlchemy<名前>Repository`命名規則に従う | 該当ファイルを確認 |
| 4 | DIが`provide_<名前>`関数 + `Annotated[..., Depends(...)]`規約に従う | `month_router.py`を確認 |
| 5 | 品目保存の都度、親`LivingExpense.amount`が品目合計に再計算される(4.4.4節ルール)実装になっている | `manage_living_expense_items.py`を確認 |
| 6 | TSV貼り付けパーサの判定規則5つ(空行無視/3分割失敗/金額非負整数でない/小分類不一致/品目名空)がすべて実装されている | `receipt_paste_parser.py`を確認 |
| 7 | Pillowによる画像デコード検証(`verify()`)が実装されている(ADR-001) | `filesystem_receipt_image_storage.py`を確認 |
| 8 | マイグレーション`010_create_living_expense_items.py`が`revision/down_revision`・カラム追加・テーブル作成・インデックスを含み、`upgrade()`/`downgrade()`両方が実装されている | ファイル内容を確認 |
| 9 | `requirements.txt`にPillow、`.gitignore`に`/data/`が追加されている | 該当ファイルを確認 |
| 10 | Won't(US-05〜11)に反する実装(外部API呼び出し・レスポンシブCSS・自動バックアップ・品目名一覧表示)がない | 追加コードをgrep確認 |
| 11 | `ruff check app tests`がエラーなしで通る | 実行ログを確認 |
| 12 | docstring・コメント・UI文言が日本語で、曖昧語のエラーメッセージがない | 追加コードを確認 |
| 13 | テストコードが本工程で新規作成されていない(ゲート6・7の担当範囲であるため) | git statusでtests/配下の新規ファイルがないことを確認 |

## 不合格時の差し戻し

- 差し戻し先: builder-impl
- 差し戻し方法: FAILとなった項目番号・該当箇所・修正内容を明記して再依頼
