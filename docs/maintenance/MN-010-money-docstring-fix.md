# MN-010: Money のdocstringが実装と矛盾していた

## 事象

- 再現手順: `app/domain/model/money.py` のdocstringと実装を突き合わせる
- 期待結果: docstringが実際の挙動を正しく説明している
- 実際の結果: クラスdocstringに「不変条件：0以上」とあるが、`__post_init__` は `pass` のみで実際には何も検証しておらず、負の値でも `Money(int)` で直接生成できる。CLAUDE.mdの設計意図（損益など負を持ちうる値はMoney(int)を直接生成する）とは実装として整合しているが、docstringの文言が「検証している」ように読め誤解を招く

## 原因

- コメントを実装に合わせて更新しないまま残していた

## 方針

- ユーザー承認: 2026-08-27（軽微項目の一括対応として）
- コード（挙動）は変更せず、docstringを実態に合わせて修正する
- 何も検証しない空の `__post_init__` は削除する（CLAUDE.mdの「不変条件は`__post_init__`で検証する」という規約はMoneyには適用されない設計のため、無意味な空メソッドを残さない）

## 修正

- `app/domain/model/money.py`: クラスdocstringを「コンストラクタは検証しない」旨に書き換え、空の `__post_init__` を削除

## ミニ検証

- `ruff check app/domain/model/money.py`: All checks passed
- `pytest tests -q`: 128 passed（`__post_init__`はもともと`pass`のみで実装的な挙動変更はないため回帰なし）
- 画面確認: なし

## 影響範囲

- `app/domain/model/money.py`
