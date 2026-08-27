"""rename food_expenses to living_expenses, add category

Revision ID: 007
Revises: 006
Create Date: 2024-01-01 00:00:00.000001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add category column (default 'food' for existing rows)
    op.add_column(
        'food_expenses',
        sa.Column('category', sa.String(length=20), nullable=False, server_default='food'),
    )
    # 2. Make location nullable
    op.alter_column(
        'food_expenses',
        'location',
        existing_type=sa.String(length=20),
        nullable=True,
    )
    # 3. Drop old index and rename table
    op.drop_index('ix_food_expenses_year_month', table_name='food_expenses')
    op.rename_table('food_expenses', 'living_expenses')
    # 4. Create index on new table
    op.create_index(
        'ix_living_expenses_year_month',
        'living_expenses',
        ['year_month'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_living_expenses_year_month', table_name='living_expenses')
    op.rename_table('living_expenses', 'food_expenses')
    op.alter_column(
        'food_expenses',
        'location',
        existing_type=sa.String(length=20),
        nullable=False,
    )
    op.drop_column('food_expenses', 'category')
    op.create_index('ix_food_expenses_year_month', 'food_expenses', ['year_month'], unique=False)
