"""create food_expenses table

Revision ID: 006
Revises: 005
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'food_expenses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('year_month', sa.String(length=7), nullable=False),
        sa.Column('location', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('note', sa.String(length=50), nullable=False, server_default=''),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_food_expenses_year_month', 'food_expenses', ['year_month'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_food_expenses_year_month', table_name='food_expenses')
    op.drop_table('food_expenses')
