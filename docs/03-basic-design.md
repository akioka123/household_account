# 基本設計書: レシート金額抽出・生活費入力の詳細化

- 日付: 2026-08-25
- 対象範囲: 本機能（レシート金額抽出・生活費入力の詳細化）専用。既存アプリ全体の基本設計は `docs/basic_design.md` を正本とし、本書はその追記点のみを扱う
- 参照元: `docs/01-user-stories.md`（US-01〜US-11、ゲート2承認済み）、`docs/02-nfr.md`（NFR-01〜09、ゲート3承認済み）、`docs/00-requirements-notes.md`、`docs/basic_design.md`（2.3節・4.3節）、プロジェクト `CLAUDE.md`
- 既存実装参照: `app/domain/model/living_expense.py`、`app/application/usecase/manage_living_expenses.py`、`app/application/port/living_expense_repository.py`、`app/presentation/web/routers/month_router.py`

---

## 1. 技術スタック

既存スタック（`docs/basic_design.md` §1、プロジェクト `CLAUDE.md`）を踏襲する。Python 3.12 / FastAPI / Jinja2 + htmx / Tailwind（CDN） / PostgreSQL（asyncpg） / SQLAlchemy 2.0 / Alembic。

本機能で新たに追加する依存は以下の1件のみ。

| 追加物 | 用途 | 根拠 |
|---|---|---|
| `Pillow`（`requirements.txt` に追加） | アップロードされた画像がデコード可能かどうかの検証（US-01） | `docs/decisions/ADR-001-receipt-image-validation-library.md` |

外部サービス・外部APIは追加しない（US-08 Wont、NFR-06）。レシート画像はファイルシステム保存（`data/receipts/`）とし、既存の `docker-compose.yml` の `.:/app` バインドマウントにより自動的にホスト側に永続化される。**`docker-compose.yml` の変更は不要**（新規 volume 追加なし、`ports` 設定の変更もなし。NFR-07に整合）。

---

## 2. ディレクトリ構成（追加・変更ファイル）

既存の4層構成（`app/domain` → `app/application` → `app/infrastructure`/`app/presentation`）に従い、以下を追加・変更する。実装（ファイル作成・変更そのもの）はゲート5で行う。本書は設計として構成のみを定義する。

```
app/
├── domain/
│   ├── model/
│   │   ├── living_expense.py              … 変更: receipt_image_path フィールド追加（MOD-02）
│   │   └── living_expense_item.py         … 新規: LivingExpenseItem, 小分類定数（MOD-01）
│   └── service/
│       └── receipt_paste_parser.py        … 新規: 貼り付けテキストのパーサ（MOD-03、純関数・データ取得なし）
├── application/
│   ├── port/
│   │   ├── living_expense_item_repository.py  … 新規: Port（MOD-04）
│   │   └── receipt_image_storage.py            … 新規: Port（MOD-05）
│   └── usecase/
│       └── manage_living_expense_items.py … 新規: ユースケース（MOD-06）
├── infrastructure/
│   ├── persistence/
│   │   ├── models/
│   │   │   ├── living_expense_model.py          … 変更: receipt_image_path カラム追加（MOD-09）
│   │   │   └── living_expense_item_model.py     … 新規: SQLAlchemyモデル（MOD-08）
│   │   └── repositories/
│   │       └── sqlalchemy_living_expense_item_repository.py … 新規（MOD-07）
│   └── storage/
│       └── filesystem_receipt_image_storage.py  … 新規: Port実装（MOD-10）
└── presentation/
    ├── web/routers/
    │   └── month_router.py                … 変更: 新規エンドポイント追加（MOD-11）
    └── templates/month/
        ├── living_tab.html                … 変更: レシート一覧・小分類集計を追加
        ├── receipt_item_form.html         … 新規: 品目手入力フォーム（品目1件追加用の部分テンプレート）
        └── receipt_paste_preview.html     … 新規: 貼り付けプレビュー編集の部分テンプレート

alembic/versions/
└── 010_create_living_expense_items.py     … 新規マイグレーション（想定連番。命名規則は6章参照）

data/
└── receipts/                              … 新規: レシート画像の保存先（ファイルシステム、DBには相対パスのみ）
```

---

## 3. 画面設計（遷移図）

新規の別画面（新規URL）は起こさない。既存の月次画面 `/month/{year}/{month}` の「生活費タブ」（`docs/basic_design.md` §2.3、URL `/month/{year}/{month}/tab/living`）を拡張し、その中の状態遷移として実現する。既存の生活費簡易入力（食費/電気代/ガス代/携帯料金/通信費、内訳なし）はそのまま残し、UI上は同じ生活費タブ内で「簡易入力（既存）」と「レシート登録（新規、食費のみ）」を別セクションとして併記する（US-05）。

### 3.1 画面要素一覧（SCR-ID）

| ID | 名称 | 位置づけ |
|---|---|---|
| SCR-01 | 生活費タブ・一覧/集計表示 | 生活費タブの初期表示状態。既存の簡易入力一覧（食費/電気代/ガス代/携帯料金/通信費）＋新規のレシート一覧（画像・品目内訳）＋新規の小分類別集計表示 |
| SCR-02 | レシート登録（画像アップロード） | 新規レシート（親 `LivingExpense`）を画像付きで作成する状態。SCR-01からの遷移先 |
| SCR-03 | 品目一覧編集（手入力・編集・削除） | 特定のレシートに対して品目を1件ずつ追加、または既存品目を編集・削除する状態 |
| SCR-04 | 貼り付け一括登録（プレビュー編集） | 品目一覧テキストを貼り付けてプレビュー表示し、保存前に行単位で修正する状態 |

### 3.2 状態遷移図

```
[月次画面 タブ切替] --GET /month/{y}/{m}/tab/living--> [SCR-01 一覧/集計]
   │
   ├─「レシートを画像付きで登録」ボタン
   │     └--> [SCR-02 画像アップロードフォーム]
   │             │ POST /month/{y}/{m}/receipts/image（画像+検証）
   │             │   ├─ 検証NG → [SCR-02にエラー表示、保存なし]（US-01 AC5）
   │             │   └─ 検証OK → 親レシート作成 → [SCR-03 品目一覧編集（新規レシート・品目0件）]
   │
   ├─「レシートを画像なしで登録（品目のみ）」ボタン
   │     └--> POST /month/{y}/{m}/receipts（画像なし）→ [SCR-03 品目一覧編集（新規レシート・品目0件）]
   │
   ├─ 各レシート行の「品目を編集」リンク
   │     └--> [SCR-03 品目一覧編集（既存レシート）]
   │             │ POST /month/{y}/{m}/receipts/{id}/items（1件追加）
   │             │ POST /month/{y}/{m}/receipt-items/{item_id}（編集）
   │             │ POST /month/{y}/{m}/receipt-items/{item_id}/delete（削除）
   │             └--> 保存の都度 [SCR-01] の一覧・集計領域を htmx で再取得
   │
   └─ SCR-03内の「貼り付けで一括登録」リンク
         └--> [SCR-04 貼り付け一括登録]
                 │ POST /month/{y}/{m}/receipts/{id}/items/paste-preview（テキスト解析、保存なし）
                 │   └--> プレビュー行（編集可能）を表示。行ごとにエラー表示（US-03 AC5）
                 │ 各行を編集 → POST /month/{y}/{m}/receipts/{id}/items/paste-save（一括保存）
                 │   ├─ 1行でも不正 → 保存せず [SCR-04にエラー表示のまま]（US-03 AC5）
                 │   └─ 全行OK → 一括保存 → [SCR-01] を再取得
```

SCR-02〜SCR-04は、いずれもURLを新規に持つ別画面ではなく、`/month/{year}/{month}/tab/living` 内の htmx 部分更新（差し替え対象は生活費タブのコンテンツ領域）として実現する。ブラウザの URL バーは `/month/{year}/{month}` のまま変化しない（既存の月次画面のタブ切替と同じ設計方針、`docs/basic_design.md` §2.3 共通タブエリア）。

### 3.3 SCR-01: 生活費タブ・一覧/集計表示

- **表示項目**
  - 既存: 簡易入力一覧（カテゴリ別、`docs/basic_design.md`の生活費簡易入力の表示をそのまま維持）。ただし食費カテゴリの一覧からは、レシート経由で作成された `LivingExpense`（`category="food"` かつ `location=""`。品目0件のものを含む）を**除外**し、下記「レシート一覧」に表示を分離する（同じ行に「場所なし」の空欄行が混在して見えることを避けるため。品目0件のレシートも除外対象に含めることで、作成直後の状態がSCR-03（品目一覧編集）へ確実に遷移できるようにする）
  - 新規: レシート一覧（対象年月内、`category="food"` かつ `location=""` の `LivingExpense`。品目0件（作成直後）を含む）
    - 各行: サムネイル（画像がある場合）/ 品目件数 / 合計金額（`LivingExpense.amount`＝品目金額の合計） / 「品目を編集」リンク / 「レシートを削除」ボタン
    - 品目名そのものは一覧に表示しない（US-10 Wont）
  - 新規: 小分類別集計表示（US-04）
    - 対象年月に登録された全 `LivingExpenseItem` を小分類ごとに合算した表（食品 / 生活用品 の2行、固定リストの全小分類を常に表示し、登録が0件の小分類は **0円として表示する**。「表示対象から除外」は採用しない。理由: 固定費一覧画面（`docs/basic_design.md`§2.5）や生活費簡易入力の既存表と同様、全カテゴリを常時表示する既存パターンに合わせ、小分類の増減に関わらず一覧性を保つため）
- **入力**
  - 「レシートを画像付きで登録」ボタン → SCR-02へ
  - 「レシートを画像なしで登録（品目のみ）」ボタン → 品目0件のレシートを作成しSCR-03へ
- **htmx部分更新**
  - タブ切替時のGET `/month/{year}/{month}/tab/living` で全体を再取得
  - 品目の追加・編集・削除・レシート削除の都度、この一覧/集計領域を再取得（NFR-02: 平均200ms以内）

### 3.4 SCR-02: レシート登録（画像アップロード）

- **入力項目**: 画像ファイル（`<input type="file" accept="image/jpeg,image/png">`）
- **操作**: 「アップロード」ボタン押下で `POST /month/{year}/{month}/receipts/image`（multipart、フィールド名 `image`）
- **検証**（US-01 AC5）
  - ファイルが空、またはPillowでのデコード検証（`PIL.Image.open().verify()`、MOD-10、ADR-001）に失敗した場合、保存を行わずエラーメッセージ「画像を読み込めませんでした。JPEGまたはPNG形式のファイルを選択してください」をSCR-02上に表示する
  - 成功時: `LivingExpense`（`category="food"`, `location=""`, `note=""`, `amount=0`, `receipt_image_path=<保存先相対パス>`）を1件作成し、SCR-03（品目0件）へ遷移する
- **画像の参照表示**（US-01 AC3: アップロードとは別のタイミングで参照可能）
  - `GET /month/{year}/{month}/receipts/{living_expense_id}/image` で画像バイナリを返す（SCR-01のレシート一覧のサムネイル・SCR-03のヘッダに表示）
- **性能**: NFR-01（平均5秒以内、5MB以下のJPEG/PNGを前提）

### 3.5 SCR-03: 品目一覧編集（手入力・編集・削除）

- **表示**: 対象レシートの画像（ある場合）、既存品目一覧（品目名・金額・小分類・編集/削除ボタン）
- **入力（手入力1件追加、US-02 AC1）**
  - 品目名（テキスト、必須）
  - 金額（数値、0以上の整数。0未満はエラーとし保存しない。US-02 AC2）
  - 小分類（プルダウン、固定リストから1つ選択。食品 / 生活用品。US-02 AC3）
  - `POST /month/{year}/{month}/receipts/{living_expense_id}/items`
- **編集（US-02 AC5）**: 各品目行の「編集」で品目名・金額・小分類をインライン編集し `POST /month/{year}/{month}/receipt-items/{item_id}` で保存
- **削除（US-02 AC6）**: 各品目行の「削除」ボタンで `POST /month/{year}/{month}/receipt-items/{item_id}/delete`
- **保存の都度**: 親レシートの `amount`（品目金額の合計、4.3節参照）を再計算し、SCR-01の一覧/集計領域を再取得
- **一覧確認（US-02 AC4）**: SCR-03自体が「対象年月に保存済みの品目データを一覧で確認できる」を満たす（レシート単位）。月全体を横断した品目一覧としては、SCR-01の小分類別集計（金額のみ、品目名は非表示）で確認する
- **性能**: NFR-02（htmx部分更新、平均200ms以内）

### 3.6 SCR-04: 貼り付け一括登録（プレビュー編集）

- **入力**: テキストエリアへの貼り付け（形式は4.4節「貼り付け形式の仕様」参照）
- **プレビュー生成**: `POST /month/{year}/{month}/receipts/{living_expense_id}/items/paste-preview`（保存は行わない、US-03 AC2）
  - レスポンスは行ごとに編集可能な入力欄（品目名・金額・小分類）を持つプレビュー表（US-03 AC3: 保存前に各行を修正できる）
  - 解析に失敗した行（タブ区切り3項目に一致しない、金額が数値でない、小分類が固定リストに一致しない）は行単位でエラー表示し、赤枠でハイライトする
- **一括保存**: `POST /month/{year}/{month}/receipts/{living_expense_id}/items/paste-save`（プレビューの編集後の全行を送信）
  - サーバ側で全行を再検証する。1行でも不正な場合は**1件も保存せず**、SCR-04にエラーメッセージ「一部の行が想定形式（品目名・金額・小分類）に一致しません。該当行を確認してください」を表示する（US-03 AC5）
  - 全行が正常な場合のみ、全品目を `LivingExpenseItem` として一括保存し、US-02と同じ保存先（`living_expense_items` テーブル）に登録する（US-03 AC4）。SCR-01を再取得する
- **性能**: NFR-02（プレビュー表示、平均200ms以内）

---

## 4. モジュール・データ設計

### 4.1 設計論点の決定（work-order 3章に対応）

#### 4.1.1 品目の小分類と既存 `LivingExpense.category` の関係（3-1）

**推奨方針のとおり決定する。**

- 小分類（食品/生活用品）は既存 `category`（`food`/`electricity`/`gas`/`mobile`/`communication`の5値固定）とは独立した、品目（レシート内の1行）に付与する新しい属性とする。既存 `category` は変更しない
- レシート登録は既存の `LivingExpense`（`category="food"`）の下に、複数の品目（品目名・金額・小分類）をぶら下げる形にする。理由: レシートは主に食料品店での買い物であり、既存の「食費」区分の内訳を詳細化するものだから（`docs/00-requirements-notes.md` カテゴリ1）。「生活用品」小分類は既存5値のどれにも該当しない支出だが、既存の枠組みを壊さず「食費レシートの中の内訳」として扱う
- 子エンティティ名は `LivingExpenseItem` とする（work-order提案どおり。他の候補として `ReceiptItem` も検討したが、`Receipt`という独立エンティティを新設しない設計（4.1.2参照。画像は `LivingExpense` の属性であり独立エンティティにしない）のため、親エンティティ名 `LivingExpense` に対応した `LivingExpenseItem` の方が命名の一貫性が高く、こちらを採用する）
- 小分類は固定リスト2種（食品/生活用品）とし、`app/domain/model/living_expense_item.py` に `LIVING_EXPENSE_CATEGORIES`（`living_expense.py`）と同じパターンで `LIVING_EXPENSE_ITEM_SUBCATEGORIES` を定義する。DB上は `VARCHAR(20)` とし、将来の小分類追加はPythonの定数リスト拡張のみで対応できる（マイグレーション不要）

#### 4.1.2 レシート画像の保存（3-2）

**推奨方針のとおり決定する。**

- ファイルシステム保存。保存先は `data/receipts/{YYYY-MM}/{living_expense_id}.{ext}`（`ext` はPillowで検証したフォーマットから `jpg`/`png` を決定）。DBには相対パス（`receipts/{YYYY-MM}/{living_expense_id}.{ext}`）のみを保持する
- 画像は `LivingExpense` に1件、1:1で紐付ける（`living_expenses.receipt_image_path` を追加、独立の `Receipt` エンティティは新設しない）。1つの `LivingExpense` に複数画像を紐付ける要件はUS-01に見当たらないため、over-engineeringしない
- `.:/app` バインドマウント（既存 `docker-compose.yml`）により `data/receipts/` はホストに永続化される。新規のvolume定義は不要
- 実装時の注意点（ゲート5向けメモ）: `data/receipts/` は個人の購買情報を含むためGit追跡対象外とする必要がある。`.gitignore` に `/data/` の追加が必要（本書は設計のみのため追加作業は実装工程で行う）

#### 4.1.3 貼り付け一括登録の入力形式（3-3）

タブ区切りテキスト（TSV）、1行1品目、列順は「品目名・金額・小分類」に決定する。

```
とうふ	108	食品
ラップ	298	生活用品
にんじん	158	食品
```

- 区切り文字: タブ文字（`\t`）。表計算ソフトやチャットのコードブロックからの貼り付けと相性がよく、目視でも列位置が揃って確認しやすいため採用する（work-order 3-3の推奨どおり、人間が確認・修正しやすい形式を優先しJSON配列形式は採らない。JSON形式は目視での列確認がしづらく、余分な引用符・波括弧の入力ミスも誘発しやすいため不採用）
- 小分類列は内部値（`grocery`/`daily_goods`）ではなく、画面表示と同じ日本語ラベル（「食品」「生活用品」）を受け付ける。理由: 貼り付け元はアプリ外でClaudeとの対話から得たテキストであり、人間が目視編集する前提のため、内部値よりも日本語ラベルの方が誤入力に気づきやすい
- ヘッダ行（列名の行）は付けない仕様とする。ヘッダ行を貼り付けた場合、金額列が数値として解析できずエラー行として扱われる（プレビュー段階でエラー表示され、保存前に利用者がその行を削除・修正できるため、ヘッダ行の特別扱いは行わない。仕様をシンプルに保つため）
- 解析・検証は `app/domain/service/receipt_paste_parser.py`（MOD-03）の純関数 `parse_receipt_paste_text(text: str) -> list[ParsedReceiptLine]` で行う（データ取得を伴わないため domain/service に置く。既存 `MonthCalculator` と同じ配置方針）
  - `ParsedReceiptLine`: `raw_line: str`, `name: str | None`, `amount: int | None`, `sub_category: str | None`, `error: str | None`
  - 判定規則:
    1. 空行は無視する（プレビュー・保存の対象に含めない）
    2. タブで分割して3項目に一致しない行 → `error="想定形式（品目名\t金額\t小分類）に一致しません"`
    3. 金額が非負整数として解析できない行 → `error="金額は0以上の整数で入力してください"`
    4. 小分類が固定リストのラベル（「食品」「生活用品」）に一致しない行 → `error="小分類は食品または生活用品のいずれかを指定してください"`
    5. 品目名が空文字の行 → `error="品目名を入力してください"`

### 4.2 モジュール一覧（MOD-ID）

| ID | モジュール | 層 | 概要 |
|---|---|---|---|
| MOD-01 | `LivingExpenseItem` / `LIVING_EXPENSE_ITEM_SUBCATEGORIES` | domain/model | 品目エンティティ（frozen dataclass）と小分類固定リスト定数 |
| MOD-02 | `LivingExpense` 拡張 | domain/model | `receipt_image_path: str \| None = None` フィールドを追加（既存フィールドの末尾、デフォルト値ありのため既存呼び出し箇所は無変更で動作） |
| MOD-03 | `parse_receipt_paste_text` | domain/service | 貼り付けテキストの解析（純関数、データ取得なし） |
| MOD-04 | `LivingExpenseItemRepository`（Port） | application/port | `find_by_living_expense_id` / `find_by_year_month`（食費レシートに紐づく品目を対象年月で取得。内部でJOIN） / `save` / `delete` / `delete_by_living_expense_id` |
| MOD-05 | `ReceiptImageStoragePort`（Port） | application/port | `validate_and_save(year, month, living_expense_id, data: bytes) -> str`（相対パスを返す。検証失敗時は `ValueError`） / `delete(relative_path: str) -> None` |
| MOD-06 | `ManageLivingExpenseItemsUseCase` | application/usecase | レシート作成（画像あり/なし）、品目の追加・編集・削除、貼り付けプレビュー・一括保存、小分類別集計取得、レシート削除 |
| MOD-07 | `SqlAlchemyLivingExpenseItemRepository` | infrastructure/persistence | MOD-04の実装（命名規則 `SqlAlchemy<名前>Repository` に準拠） |
| MOD-08 | `LivingExpenseItemModel` | infrastructure/persistence/models | `living_expense_items` テーブルのSQLAlchemyモデル |
| MOD-09 | `LivingExpenseModel` 拡張 | infrastructure/persistence/models | `receipt_image_path` カラム追加（`String(255)`, nullable） |
| MOD-10 | `FilesystemReceiptImageStorage` | infrastructure/storage | MOD-05の実装。Pillowでのデコード検証（ADR-001）、`data/receipts/{YYYY-MM}/{id}.{ext}` への保存・削除 |
| MOD-11 | `month_router.py` 拡張 | presentation/web/routers | 新規エンドポイント群、`provide_living_expense_item_repo` / `provide_receipt_image_storage` / `provide_manage_living_expense_items_uc`（DI規約 `provide_<名前>` + `Annotated[..., Depends(...)]` に準拠） |
| MOD-12 | テンプレート拡張 | presentation/templates | `living_tab.html` 拡張、`receipt_item_form.html` / `receipt_paste_preview.html` 新規 |

### 4.3 エンドポイント一覧（MOD-11詳細）

| メソッド | パス | 概要 | 対応SCR |
|---|---|---|---|
| GET | `/month/{year}/{month}/tab/living` | 生活費タブ全体（既存拡張） | SCR-01 |
| POST | `/month/{year}/{month}/receipts` | レシート新規作成（画像なし） | SCR-01→SCR-03 |
| POST | `/month/{year}/{month}/receipts/image` | レシート新規作成（画像付き、multipart） | SCR-02 |
| GET | `/month/{year}/{month}/receipts/{living_expense_id}/image` | 保存済み画像の参照表示 | SCR-01, SCR-02, SCR-03 |
| POST | `/month/{year}/{month}/receipts/{living_expense_id}/delete` | レシート（親＋品目全件＋画像ファイル）削除 | SCR-01 |
| POST | `/month/{year}/{month}/receipts/{living_expense_id}/items` | 品目を1件追加 | SCR-03 |
| POST | `/month/{year}/{month}/receipt-items/{item_id}` | 品目を編集 | SCR-03 |
| POST | `/month/{year}/{month}/receipt-items/{item_id}/delete` | 品目を削除 | SCR-03 |
| POST | `/month/{year}/{month}/receipts/{living_expense_id}/items/paste-preview` | 貼り付けテキストを解析しプレビュー返却（保存なし） | SCR-04 |
| POST | `/month/{year}/{month}/receipts/{living_expense_id}/items/paste-save` | プレビュー確定後の一括保存 | SCR-04 |

既存の生活費簡易入力のエンドポイント（`POST /month/{year}/{month}/living-expenses` 等）は無変更のまま維持する（US-05）。

### 4.4 データ設計（DB）

#### 4.4.1 既存テーブル変更: `living_expenses`

| カラム | 型 | 制約 | 備考 |
|---|---|---|---|
| `receipt_image_path` | `VARCHAR(255)` | NULL可 | 新規追加。`data/receipts/` からの相対パス。画像なしレシート・既存の簡易入力行は NULL |

既存の `amount` カラムは、品目1件以上を持つレシート行については**品目金額の合計値を都度反映**する（4.4.4節参照）。既存の簡易入力行（品目を持たない行）は従来どおり手入力値をそのまま保持する。この方式により、月次サマリ・年次ダッシュボードの「生活費（食費）合計」計算（既存の `ManageLivingExpensesUseCase.get_living_expense_data` が `LivingExpense.amount` を集計する処理、`docs/basic_design.md`の生活費集計と同一）は無変更のまま、レシート由来の品目合計も正しく合算される。

#### 4.4.2 新規テーブル: `living_expense_items`

| カラム | 型 | 制約 | 備考 |
|---|---|---|---|
| `id` | `INTEGER` | PK, autoincrement | |
| `living_expense_id` | `INTEGER` | NOT NULL, FK → `living_expenses.id`, `ON DELETE CASCADE` | 親レシート。CASCADE削除により、親（レシート）削除時に品目も自動削除される（MOD-06のレシート削除処理と整合） |
| `name` | `VARCHAR(100)` | NOT NULL | 品目名 |
| `amount` | `INTEGER` | NOT NULL | 金額。0以上（アプリ層＝MOD-06で検証。US-02 AC2） |
| `sub_category` | `VARCHAR(20)` | NOT NULL | 小分類の内部値（`grocery` / `daily_goods`） |

インデックス: `living_expense_id` に単純インデックスを1つ付与する（`ix_living_expense_items_living_expense_id`、品目取得の外部キー検索用）のみとする。NFR-08（想定規模: 月20〜30件、年300件程度）を前提に、`sub_category` への追加インデックスや複合インデックスは行わない（この規模ではフルスキャンでも性能要件（NFR-02/NFR-03）を満たすため、過剰なインデックス設計をしない）。

#### 4.4.3 マイグレーション

- ファイル名: `alembic/versions/010_create_living_expense_items.py`（連番規則 `<3桁連番>_<説明>.py` に準拠。直近は `009_add_unique_to_fixed_item_histories.py` のため次番は `010`）
- `revision = '010'`, `down_revision = '009'`
- 内容: (1) `living_expenses` に `receipt_image_path` カラムを追加、(2) `living_expense_items` テーブルを新規作成し `ix_living_expense_items_living_expense_id` を作成
- 実際のファイル作成・`upgrade()`/`downgrade()` の実装はゲート5（実装工程）で行う。本書では設計のみを定義する

#### 4.4.4 品目保存時の親レシート整合ルール（MOD-06の内部ルール）

- 品目の追加・編集・削除のいずれの操作後も、対象 `living_expense_id` の `LivingExpense.amount` を「その `living_expense_id` に紐づく `LivingExpenseItem.amount` の合計」に再計算して保存する
- レシート新規作成時（画像あり/なし）の初期 `amount` は `0`（品目が0件のため）
- レシートの `location` は空文字とする。既存の `ManageLivingExpensesUseCase.add_living_expense`（食費は場所必須のバリデーションを持つ）は経由せず、MOD-06が独自に `LivingExpense` を生成・更新するため、レシート由来の行には既存の「食費は場所必須」バリデーションを適用しない（レシートには店舗名等の入力項目がUS-01/02のAC上存在しないため）

### 4.5 NFR達成方針（該当モジュールでの言及）

| NFR | 該当モジュール | 方針 |
|---|---|---|
| NFR-01（画像アップロード5秒以内） | MOD-05, MOD-10, MOD-11 | ローカルDocker上でのファイルI/O＋Pillowデコード検証のみで、外部通信を伴わないため5秒以内は十分達成可能な処理量（5MB以下のJPEG/PNG 1枚） |
| NFR-02（一覧・プレビュー200ms） | MOD-04, MOD-06, MOD-07 | 月20〜30件規模のクエリはインデックス（4.4.2節）ありの単純SELECTで完結し、200ms以内は達成可能 |
| NFR-03（集計表示300ms） | MOD-04, MOD-06, MOD-07 | 年300件規模のJOIN集計であり、追加インデックスなしでも300ms以内は達成可能（NFR-08の想定規模） |
| NFR-04（RTO7日） | — | 新規の監視・アラート機構は追加しない（設計要素なし、既存運用のまま） |
| NFR-05（pg_dump運用維持） | — | 新規バックアップ機構は追加しない。**注意点**: レシート画像は `data/receipts/`（ファイルシステム）に保存され、`pg_dump`（PostgreSQLのみ対象）のバックアップ範囲には含まれない。NFR-05は「新規の定期バックアップ機構を追加しない」ことを求めており本設計もこれに従うが、画像がpg_dump運用では復旧できない点は運用上の既知の制約として明記する（新たな設計対応は行わない） |
| NFR-06（運用費0円） | 1章 | Pillowは無償のオープンソースライブラリ、外部API・SaaSを追加しない（ADR-001） |
| NFR-07（非公開） | 1章 | `docker-compose.yml` の `ports` 変更なし。`data/receipts/` はコンテナ内のみで完結し、外部公開しない |
| NFR-08（保守性・想定規模） | 4.4.2節 | 追加インデックスを最小限（FK検索用の1つのみ）にとどめる |
| NFR-09（PC限定・1024px以上） | 3章全体 | SCR-01〜04はいずれも既存の月次画面と同じデスクトップ幅レイアウトを前提とし、レスポンシブ対応は行わない |

---

## 5. 外部連携

本機能に外部API・外部サービスとの連携は**存在しない**（US-08 Wont、NFR-06）。

- レシート画像の読み取り（品目データ化）はアプリ外でユーザーが手動でClaude等を操作して行い、その結果テキストをUS-03の貼り付け機能でアプリ内に取り込む運用とする。アプリからClaude等への自動呼び出しは行わない
- レシート画像の保存はアプリ内部のローカルファイルI/O（`data/receipts/`）であり、外部ストレージサービス（S3等）への連携は行わない
- カード請求の自動読取・CSV連携（US-06 Wont）、OCR/ML自動抽出（US-07 Wont）は本機能のスコープ外であり、対応する外部連携設計も存在しない

---

## 6. トレーサビリティ表

`traceability` スキル準拠。実装・テストの各列はゲート5〜7で埋まる（本書は設計工程の成果物のため、設計時点では未着手＝空欄で正しい。Mustストーリーの「設計」列に空欄がないことを本工程の完了条件とする）。

| US/NFR | 設計(SCR/MOD) | 実装(ファイル) | 単体(UT) | 結合(IT) | システム(ST) |
|---|---|---|---|---|---|
| US-01（Must） | SCR-02, MOD-02, MOD-05, MOD-06, MOD-09, MOD-10, MOD-11, MOD-12 | — | — | — | — |
| US-02（Must） | SCR-01, SCR-03, MOD-01, MOD-02, MOD-04, MOD-06, MOD-07, MOD-08, MOD-11, MOD-12 | — | — | — | — |
| US-03（Should） | SCR-04, MOD-01, MOD-03, MOD-04, MOD-06, MOD-07, MOD-08, MOD-11, MOD-12 | — | — | — | — |
| US-04（Must） | SCR-01, MOD-01, MOD-04, MOD-06, MOD-07, MOD-11, MOD-12 | — | — | — | — |
| US-05（Wont・共存確認） | SCR-01（既存簡易入力の表示区分）, 4.3節（既存エンドポイント無変更） | — | — | — | — |
| US-06（Wont） | 対象外（カード請求自動読取の設計要素なし。5章参照） | — | — | — | — |
| US-07（Wont） | 対象外（OCR/ML設計要素なし。5章参照） | — | — | — | — |
| US-08（Wont） | 対象外（外部API呼び出し設計要素なし。5章参照） | — | — | — | — |
| US-09（Wont） | 対象外（レスポンシブ対応の設計要素なし。NFR-09で明記） | — | — | — | — |
| US-10（Wont） | SCR-01（品目名は集計に含めるが一覧表示しない設計） | — | — | — | — |
| US-11（Wont） | 対象外（新規バックアップ機構の設計要素なし。NFR-05参照） | — | — | — | — |
| NFR-01 | SCR-02, MOD-05, MOD-10, MOD-11 | — | — | — | — |
| NFR-02 | SCR-01, SCR-04, MOD-04, MOD-06, MOD-07 | — | — | — | — |
| NFR-03 | SCR-01, MOD-04, MOD-07 | — | — | — | — |
| NFR-04 | 対象外（設計要素なし。4.5節参照） | — | — | — | — |
| NFR-05 | 4.5節（画像バックアップ対象外である旨の明記のみ、設計変更なし） | — | — | — | — |
| NFR-06 | 1章（ADR-001）、5章 | — | — | — | — |
| NFR-07 | 1章、5章 | — | — | — | — |
| NFR-08 | 4.4.2節 | — | — | — | — |
| NFR-09 | 3章全体 | — | — | — | — |

**カバレッジ確認**: US-01〜US-11（11件）・NFR-01〜09（9件）の全20件がこの表に反映されている。Must（US-01, US-02, US-04）はいずれも「設計」列が空欄でない（カバー漏れなし）。Wont（US-05〜11）は該当なしの理由を明記した。
