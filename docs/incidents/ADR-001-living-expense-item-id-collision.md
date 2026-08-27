---
id: ADR-001
title: 生活費品目(レシート品目)のID採番をレシート単位から全体一意へ変更する
status: 承認済
date: 2026-08-27
supersedes: null
superseded_by: null
tags: [bug, receipt, living-expense-item, id-collision]
---

# ADR-001: 生活費品目(レシート品目)のID採番をレシート単位から全体一意へ変更する

- 日付: 2026-08-27 / 状態: 承認済

## 背景(Why)

ユーザー報告: 「レシートの品目を追加すると、他のレシートの品目が削除される」。

再現手順:
1. レシートAに品目を1件追加する(1件目のため id=1 で保存される)
2. レシートBに品目を1件追加する(レシートB側も1件目のため id=1 で採番される)
3. レシートAの品目一覧を見ると、追加したはずの品目が消えている(実際にはレシートBの内容で
   上書きされている)

影響範囲: `app/application/usecase/manage_living_expense_items.py` の `add_item()` /
`save_paste()` を経由する全ての品目追加操作(通常追加・貼り付け一括登録の両方)。

## 原因

`living_expense_items` テーブルの `id` は `autoincrement=True` の**テーブル全体で一意な主キー**
(`app/infrastructure/persistence/models/living_expense_item_model.py:15`)。

一方、`ManageLivingExpenseItemsUseCase.add_item()`
(`app/application/usecase/manage_living_expense_items.py:159-181`) は次のように
**追加対象レシートに紐づく品目だけ**を見て次IDを計算していた。

```python
existing = await self._living_expense_item_repo.find_by_living_expense_id(
    command.living_expense_id
)
next_id = max([i.id for i in existing], default=0) + 1
```

`find_by_living_expense_id` はそのレシートの品目のみを返すため、**どのレシートでも1件目の
品目は必ず id=1** になる。`save_paste()` (同ファイル 216-258行目) も同じパターン。

さらに `SqlAlchemyLivingExpenseItemRepository.save()`
(`app/infrastructure/persistence/repositories/sqlalchemy_living_expense_item_repository.py:51-72`)
は `living_expense_id` を条件に含めず **`id` のみで既存行を検索してUPSERT**する。

```python
stmt = select(LivingExpenseItemModel).where(LivingExpenseItemModel.id == item.id)
...
if model:
    model.living_expense_id = item.living_expense_id  # 他レシートの行を書き換えてしまう
```

この2つが組み合わさり、レシート間で id が衝突すると、後から保存した方が先に保存されていた
別レシートの品目行を `living_expense_id` ごと上書きする。「他レシートの品目が削除される」
という報告は、実際には上書きによる乗っ取りである。

なお、親エンティティ `LivingExpense` の採番(`_next_living_expense_id()`、同ファイル
319-322行目)は `find_all()` でテーブル全体を見てから採番しており、こちらは正しい実装。
品目側だけがレシート単位スコープの誤った採番になっていた。

## 決定(What)

品目のID採番を、親エンティティと同じ「テーブル全体を見てから採番する」方式に統一する。

- `LivingExpenseItemRepository` に `find_all()` を追加する(`LivingExpenseRepository.find_all()`
  と同じ役割)
- ユースケースに `_next_living_expense_item_id()` を追加し、`find_all()` の結果から
  `max(id)+1` を計算する
- `add_item()` / `save_paste()` の採番箇所をこの新メソッドに置き換える

`save()` のUPSERT実装(`id`のみで検索)自体は変更しない。採番が全体一意である限り、
主キーによるUPSERTは正しく機能するため。

## 実施方法(How)

- `app/application/port/living_expense_item_repository.py`: `find_all()` をProtocolに追加
- `app/infrastructure/persistence/repositories/sqlalchemy_living_expense_item_repository.py`:
  `find_all()` を実装(`LivingExpenseItemModel` 全件をid順で取得)
- `app/application/usecase/manage_living_expense_items.py`: `_next_living_expense_item_id()`
  を追加し、`add_item()` / `save_paste()` の採番ロジックを置き換え
- `tests/unit/application/test_manage_living_expense_items.py`:
  既存の採番関連テスト(`test_add_item_recalculates_parent_amount` /
  `test_save_paste_saves_all_when_all_lines_valid`)のモックを新しい採番経路
  (`find_all`)に合わせて更新
  再発防止の回帰テスト`test_add_item_id_is_unique_across_receipts_regression`を追加。
  既に他レシートに id=1 の品目が存在する状態で、別レシートへの初回追加が id=1 と衝突せず
  `max+1` になることを検証する
- 検証: `./venv/Scripts/python.exe -m pytest tests -q` および
  `./venv/Scripts/python.exe -m ruff check app tests` を実行し、全件パスを確認する

### 検証結果(2026-08-27)

- `pytest tests -q`: **181 passed**(既存180件 + 回帰テスト1件追加)
- `ruff check app tests`: 今回の変更ファイル(`app/application/port/living_expense_item_repository.py` /
  `app/infrastructure/persistence/repositories/sqlalchemy_living_expense_item_repository.py` /
  `app/application/usecase/manage_living_expense_items.py` /
  `tests/unit/application/test_manage_living_expense_items.py`)に新規の指摘なし。
  他ファイルに既存の指摘22件があるが、本修正の対象外(別issue)

## 採らなかった選択肢と理由(Why not)

- **DBのautoincrementに採番を委ね、保存後にIDを読み戻す方式**: より堅牢だが、
  `LivingExpenseItemRepository.save()` の戻り値をvoidから保存後アイテムに変更する必要があり、
  `LivingExpense`側の既存パターン(先に採番してから保存)とも非対称になる。影響範囲が
  ドメインモデル・Port・全呼び出し元に及ぶため、hotfix-flowが想定する「軽微な修正」の
  範囲を超える。将来的な設計改善候補として次項に残す
- **`living_expense_id` をUPSERTのWHERE条件に含める**: 衝突自体は起きたままになり、
  「追加したのに保存されない(サイレント失敗)」という別の不具合に置き換わるだけで根本解決にならない
- **`find_by_year_month` で当該月内のみ一意にする**: 月をまたぐ品目移動やレシート再割当のような
  将来変更で再び衝突しうる。テーブル全体で一意にする方が安全でシンプル

## しないこと(スコープ除外)

- `LivingExpense`(親)側の採番方式(`_next_living_expense_id()`)の変更は行わない
  (既に正しく実装されているため対象外)
- DBのautoincrementへの全面移行(上記「採らなかった選択肢」参照)は本ADRの対象外とする
- `docs/maintenance/` のMN形式との統合・使い分けルールの見直しは対象外
  (`docs/incidents/CLAUDE.md` に暫定の使い分けを記載済み)

## 再検討条件

- 同種の「レシート単位/月単位でスコープした採番」による衝突が他のエンティティでも見つかった場合、
  DBのautoincrementへの全面移行を再検討する
- 同時アクセス(複数タブからの同時追加)によるレースコンディションが実運用で問題になった場合、
  採番方式そのもの(アプリ側でのmax+1計算)を再検討する(本ADRはID重複の解消のみを扱い、
  複数同時アクセス時の競合状態は元々本アプリの想定スコープ外)

---

## 運用ルールの反映(このADR作成に伴う決定)

今後もhotfix-flowでの修正着手前にこのディレクトリへADRを作成する運用を徹底するため、
「スキル化」と「プロジェクトCLAUDE.mdへの追記」のどちらを採るかを検討した。

- **スキル化(新規skill or 既存hotfix-flowへの追記)を採らない理由**: hotfix-flowは
  グローバル共通スキル(`~/.claude/skills/hotfix-flow/`)であり、他の全プロジェクトからも
  利用される。`docs/incidents/` というADR形式での記録は household_account 固有の運用
  (`docs/decisions/` の命名・フロントマター規約を踏襲した本プロジェクト独自の拡張)であり、
  他プロジェクトに一律適用すると `docs/decisions/` を持たないプロジェクトで規約が
  成立しない。グローバルCLAUDE.mdの配置判定基準(「他プロジェクトでも使うか？」)に照らし、
  NOと判断
- **プロジェクトCLAUDE.mdへの追記を採る理由**: 本プロジェクトのCLAUDE.mdは全セッションで
  必ずコンテキストに読み込まれるため、スキルのトリガー判定(説明文とのマッチング)に
  依存せず確実に適用される。追記内容は数行の短い手順参照で済み、新規skillファイルを
  作成・保守するコストと比べてトークン・保守コストの両方で安い
- 結論: `CLAUDE.md` の「工程」節に、hotfix-flow着手前は `docs/incidents/` の運用に従う旨を
  追記する(本ADRと同一コミットで反映)
