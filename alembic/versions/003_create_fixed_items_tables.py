"""create fixed_items and fixed_item_histories tables

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'fixed_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'fixed_item_histories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fixed_item_id', sa.Integer(), nullable=False),
        sa.Column('effective_from', sa.String(length=7), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('card_id', sa.Integer(), nullable=True),
        sa.Column('included_in_card', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['fixed_item_id'], ['fixed_items.id'], ),
        sa.ForeignKeyConstraint(['card_id'], ['cards.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_fixed_item_histories_fixed_item_id', 'fixed_item_histories', ['fixed_item_id'], unique=False)
    op.create_index('ix_fixed_item_histories_effective_from', 'fixed_item_histories', ['effective_from'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_fixed_item_histories_effective_from', table_name='fixed_item_histories')
    op.drop_index('ix_fixed_item_histories_fixed_item_id', table_name='fixed_item_histories')
    op.drop_table('fixed_item_histories')
    op.drop_table('fixed_items')

