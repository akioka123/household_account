# 作業指示書: ゲート7（結合テスト）— レシート金額抽出・生活費入力の詳細化

- 宛先: builder-test
- 工程: integration-test（ゲート7）
- 発行: 統括（トークン節約モードによりpm役を代行）
- 対象: `TestClient` + `app.dependency_overrides` を用いた結合テスト（DBなし。プロジェクトCLAUDE.mdの既存規約どおり）

## 1. 読むべき入力

1. `docs/03-basic-design.md` 4.3節（エンドポイント一覧、10本）、3章（画面遷移・状態遷移図）
2. `docs/01-user-stories.md`（US-01〜04, US-03の受け入れ基準）
3. `app/presentation/web/routers/month_router.py`（新規エンドポイントの実装、DI関数名）
4. 既存の結合テスト（作法の踏襲）: `tests/integration/` 配下の既存テスト（`TestClient` + `app.dependency_overrides` で `ManageLivingExpensesUseCase` 等を差し替えるパターン）
5. プロジェクト `CLAUDE.md`（結合テストはDBなしで動かす規約）

## 2. テスト対象（4.3節のエンドポイント10本）

`app.dependency_overrides` で `ManageLivingExpenseItemsUseCase`（および画像ストレージ・リポジトリ、必要に応じて）をモックに差し替え、以下を検証する。

| エンドポイント | 検証観点 |
|---|---|
| `GET /month/{y}/{m}/tab/living` | 生活費タブの応答に既存簡易入力一覧・レシート一覧・小分類別集計が含まれる |
| `POST /month/{y}/{m}/receipts`（画像なし） | レシート作成が呼ばれ、応答にSCR-03相当の内容（品目0件の編集領域）が含まれる |
| `POST /month/{y}/{m}/receipts/image` | multipart送信でユースケースの画像あり作成が呼ばれる。画像検証失敗時（ユースケースが例外を投げるケース）にエラー応答になること |
| `GET /month/{y}/{m}/receipts/{id}/image` | 画像バイナリが返る（Content-Type等） |
| `POST /month/{y}/{m}/receipts/{id}/delete` | レシート削除が呼ばれ、一覧が更新された応答になる |
| `POST /month/{y}/{m}/receipts/{id}/items` | 品目追加が呼ばれ、応答に追加後の一覧・集計が反映される |
| `POST /month/{y}/{m}/receipt-items/{item_id}` | 品目編集が呼ばれる |
| `POST /month/{y}/{m}/receipt-items/{item_id}/delete` | 品目削除が呼ばれる |
| `POST /month/{y}/{m}/receipts/{id}/items/paste-preview` | 貼り付けテキストの解析結果（プレビュー、保存なし）が応答に含まれる |
| `POST /month/{y}/{m}/receipts/{id}/items/paste-save` | 全行正常なら一括保存が呼ばれる／不正行を含む場合は保存が呼ばれずエラー応答になる（US-03 AC5） |

## 3. 特に検証すること（画面遷移・状態整合性）

- `docs/03-basic-design.md` 3.2節の状態遷移どおりに、各操作後のレスポンスが期待するSCR状態（一覧再取得・品目編集領域の表示等）を返すこと
- ゲート5で修正した「レシート作成直後（品目0件）でも一覧・編集領域に到達できる」ことを、エンドポイントレベルでも検証する（`POST /receipts` 直後のレスポンスに作成したレシートの編集領域が含まれること）
- 既存の生活費簡易入力エンドポイント（変更していないもの）が本機能追加によって壊れていないことを確認する回帰テストを最低限含める

## 4. 完了条件

- `tests/integration/` 配下に新規テストファイルを作成し、`./venv/Scripts/python.exe -m pytest tests/integration -q` を実行してすべて成功することを確認する（venvがこのworktreeに無い場合はメインリポジトリの `C:\projects\household_account\venv\Scripts\python.exe` を使う）
- `./venv/Scripts/python.exe -m pytest tests -q`（全体）で回帰がないことを確認する
- `./venv/Scripts/python.exe -m ruff check app tests` でlintエラーがないことを確認する
- 完了したら統括に、作成したテストファイル一覧・テストケース数・実行結果を報告する
