# 作業指示書: ゲート5（実装）— レシート金額抽出・生活費入力の詳細化

- 宛先: builder-impl
- 工程: impl（ゲート5）
- 発行: 統括（トークン節約モードによりpm役を代行）
- 対象: `docs/03-basic-design.md` の設計を実装する。**本工程はプロダクトコードのみ**。単体テスト(tests/unit)・結合テスト(tests/integration)はゲート6・7でbuilder-testが担当するため、ここでは書かない（テストファイルを新規作成しないこと）

## 1. 読むべき入力

1. `docs/03-basic-design.md`（全章。特に2章ディレクトリ構成、4章モジュール・データ設計）
2. `docs/decisions/ADR-001-receipt-image-validation-library.md`
3. 既存実装（参考パターンとして踏襲）: `app/domain/model/living_expense.py`, `app/application/usecase/manage_living_expenses.py`, `app/application/port/living_expense_repository.py`, `app/infrastructure/`配下の対応する既存Repository実装・SQLAlchemyモデル, `app/presentation/web/routers/month_router.py`, `app/presentation/templates/month/`配下の既存テンプレート, 直近のalembicマイグレーション（`alembic/versions/009_*.py`）
4. プロジェクト `CLAUDE.md`（実装の約束: frozen dataclass・`__post_init__`検証、Port命名規則、DI規約、日本語docstring/コメント/UI文言）

## 2. 実装対象（基本設計 4.2節 MOD-01〜12 に対応）

以下を基本設計の記述どおりに実装する。ファイルパス・クラス名・関数シグネチャは `docs/03-basic-design.md` の該当節に従う。

| MOD | 実装内容 | 基本設計の参照節 |
|---|---|---|
| MOD-01 | `app/domain/model/living_expense_item.py`: `LivingExpenseItem`(frozen dataclass) + `LIVING_EXPENSE_ITEM_SUBCATEGORIES`定数（`grocery`=食品, `daily_goods`=生活用品） | 4.1.1, 4.2 |
| MOD-02 | `app/domain/model/living_expense.py` に `receipt_image_path: str \| None = None` を追加（既存フィールド末尾。既存の呼び出し箇所は無変更で動作すること） | 4.2 |
| MOD-03 | `app/domain/service/receipt_paste_parser.py`: `parse_receipt_paste_text(text: str) -> list[ParsedReceiptLine]`。判定規則5つ（空行無視、タブ3分割失敗、金額非負整数でない、小分類ラベル不一致、品目名空）は4.1.3節の記載どおり実装する | 4.1.3 |
| MOD-04 | `app/application/port/living_expense_item_repository.py`: `LivingExpenseItemRepository`(Protocol)。`find_by_living_expense_id` / `find_by_year_month` / `save` / `delete` / `delete_by_living_expense_id` | 4.2 |
| MOD-05 | `app/application/port/receipt_image_storage.py`: `ReceiptImageStoragePort`(Protocol)。`validate_and_save(year, month, living_expense_id, data: bytes) -> str` / `delete(relative_path: str) -> None` | 4.2 |
| MOD-06 | `app/application/usecase/manage_living_expense_items.py`: `ManageLivingExpenseItemsUseCase`。レシート作成(画像あり/なし)、品目の追加・編集・削除、貼り付けプレビュー・一括保存、小分類別集計取得、レシート削除。**4.4.4節の親レシート整合ルール（品目保存の都度、親`LivingExpense.amount`を品目合計で再計算）を必ず実装すること**。既存の`ManageLivingExpensesUseCase.add_living_expense`は経由せず、レシート由来の`LivingExpense`は独自に生成・更新する（食費の場所必須バリデーションを適用しない、4.4.4節） | 3.4〜3.6, 4.4.4 |
| MOD-07 | `app/infrastructure/persistence/repositories/sqlalchemy_living_expense_item_repository.py`: MOD-04実装（命名規則`SqlAlchemy<名前>Repository`） | 4.2 |
| MOD-08 | `app/infrastructure/persistence/models/living_expense_item_model.py`: `living_expense_items`テーブルのSQLAlchemyモデル（4.4.2節のカラム定義どおり） | 4.4.2 |
| MOD-09 | 既存の`LivingExpenseModel`に`receipt_image_path`カラム追加（`String(255)`, nullable） | 4.4.1 |
| MOD-10 | `app/infrastructure/storage/filesystem_receipt_image_storage.py`: MOD-05実装。`PIL.Image.open(io.BytesIO(data)).verify()`で検証（ADR-001）。保存先`data/receipts/{YYYY-MM}/{living_expense_id}.{ext}` | 4.1.2, ADR-001 |
| MOD-11 | `app/presentation/web/routers/month_router.py` に4.3節のエンドポイント一覧（GET/POST 10本）を追加。DI関数`provide_living_expense_item_repo` / `provide_receipt_image_storage` / `provide_manage_living_expense_items_uc`を`provide_<名前>`規約で追加 | 4.3 |
| MOD-12 | テンプレート: `app/presentation/templates/month/living_tab.html`拡張（レシート一覧・小分類別集計・両ボタン追加）、`receipt_item_form.html`新規（品目追加/編集フォーム部分テンプレート）、`receipt_paste_preview.html`新規（貼り付けプレビュー編集） | 3.3〜3.6 |

## 3. その他の実装作業

- `requirements.txt` に `Pillow>=10.0.0,<12.0.0` を追加（ADR-001）
- `.gitignore` に `/data/` を追加（レシート画像はGit追跡対象外。基本設計4.1.2節の実装時注意点）
- マイグレーション: `alembic/versions/010_create_living_expense_items.py`（`revision='010'`, `down_revision='009'`）。(1) `living_expenses`に`receipt_image_path`列追加 (2) `living_expense_items`テーブル作成 (3) `ix_living_expense_items_living_expense_id`インデックス作成。`upgrade()`/`downgrade()`両方を実装する

## 4. 遵守事項

- 4層アーキテクチャの依存方向（presentation → application → domain、infrastructure → application/domain）を守ること
- ドメインモデルは`@dataclass(frozen=True)`。不変条件（金額0以上等）は`__post_init__`で検証すること
- docstring・コメント・UI文言はすべて日本語
- 曖昧語のUI文言（「適切に」「高速に」等）を使わない。エラーメッセージは基本設計3.4〜3.6節の文言をそのまま使う
- US-05〜US-11（Won't確定済み）に反する実装をしない：外部API呼び出しコード、スマホ向けレスポンシブCSS、自動バックアップ処理、品目名を月次画面へ一覧表示する処理などを追加しないこと
- テストコードは書かない（ゲート6・7で別途実施）。ただし実装が最低限動作することは、必要であれば手動確認（`docker compose up -d`起動確認、簡単なリクエスト送信等）で構わない

## 5. 完了条件

- MOD-01〜MOD-12、マイグレーション、requirements.txt、.gitignoreの変更を終えたら統括に完了報告する
- `./venv/Scripts/python.exe -m ruff check app tests` を実行し、新規コードにlintエラーがないことを確認してから報告する
- 設計からの逸脱（実装時に発見した設計の不整合・変更が必要だった箇所）があれば、理由とともに報告に含めること
