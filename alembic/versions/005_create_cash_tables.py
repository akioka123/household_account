"""create cash_balances and withdrawals tables

Revision ID: 005
Revises: 004
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'cash_balances',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('year_month', sa.String(length=7), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('year_month', name='uq_cash_balances_year_month')
    )
    
    op.create_index('ix_cash_balances_year_month', 'cash_balances', ['year_month'], unique=True)
    
    op.create_table(
        'withdrawals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('year_month', sa.String(length=7), nullable=False),
        sa.Column('withdrawal_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('note', sa.String(length=200), nullable=False, server_default=''),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_withdrawals_year_month', 'withdrawals', ['year_month'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_withdrawals_year_month', table_name='withdrawals')
    op.drop_table('withdrawals')
    op.drop_index('ix_cash_balances_year_month', table_name='cash_balances')
    op.drop_table('cash_balances')
