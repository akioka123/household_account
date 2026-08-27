"""create living_expense_items table and receipt_image_path column

レシート金額抽出・生活費入力の詳細化（US-01〜US-04）のためのマイグレーション。
(1) living_expenses に receipt_image_path 列を追加
(2) living_expense_items テーブルを新規作成
(3) ix_living_expense_items_living_expense_id インデックスを作成

Revision ID: 010
Revises: 009
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # (1) living_expenses に receipt_image_path 列を追加
    op.add_column(
        'living_expenses',
        sa.Column('receipt_image_path', sa.String(length=255), nullable=True),
    )

    # (2) living_expense_items テーブルを新規作成
    op.create_table(
        'living_expense_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('living_expense_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('sub_category', sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['living_expense_id'],
            ['living_expenses.id'],
            ondelete='CASCADE',
        ),
    )

    # (3) ix_living_expense_items_living_expense_id インデックスを作成
    op.create_index(
        'ix_living_expense_items_living_expense_id',
        'living_expense_items',
        ['living_expense_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        'ix_living_expense_items_living_expense_id',
        table_name='living_expense_items',
    )
    op.drop_table('living_expense_items')
    op.drop_column('living_expenses', 'receipt_image_path')
