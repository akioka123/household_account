"""固定費履歴に (fixed_item_id, effective_from) の一意制約を追加

同一の固定費項目・同一の適用開始年月に対する金額は1つに定まるべきだが、
これまで一意制約が無く、同月内の訂正が新しい行として追加されていた。
FixedExpenses.get_effective_histories() は適用開始年月を厳密な `>` で比較するため、
同着の場合は先に取得された行（＝IDの小さい古い行）が採用され、
後から入力した訂正が黙って無視されていた。

incomes / card_statements / cash_balances / month_notes と同じく
「その年月の状態は1行」という規約に揃える。

既存の重複行は、各 (fixed_item_id, effective_from) で最大IDの行（＝最後の操作）
のみを残して削除する。

Revision ID: 009
Revises: 008
"""

from typing import Sequence, Union

from alembic import op

revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UNIQUE_CONSTRAINT_NAME = 'uq_fixed_item_histories_item_effective_from'


def upgrade() -> None:
    """重複行を整理してから一意制約を追加する"""
    # 同一 (fixed_item_id, effective_from) で最大ID以外を削除する（最後の操作を残す）
    op.execute(
        """
        DELETE FROM fixed_item_histories AS older
        USING fixed_item_histories AS newer
        WHERE older.fixed_item_id = newer.fixed_item_id
          AND older.effective_from = newer.effective_from
          AND older.id < newer.id
        """
    )

    op.create_unique_constraint(
        UNIQUE_CONSTRAINT_NAME,
        'fixed_item_histories',
        ['fixed_item_id', 'effective_from'],
    )


def downgrade() -> None:
    """一意制約を外す

    注意: upgrade で削除した重複行は復元できない。
    """
    op.drop_constraint(
        UNIQUE_CONSTRAINT_NAME,
        'fixed_item_histories',
        type_='unique',
    )
