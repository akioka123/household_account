"""create incomes table

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'incomes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('year_month', sa.String(length=7), nullable=False),
        sa.Column('salary_gross', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('salary_net', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('bonus_gross', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('bonus_net', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('year_month')
    )
    op.create_index('ix_incomes_year_month', 'incomes', ['year_month'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_incomes_year_month', table_name='incomes')
    op.drop_table('incomes')

