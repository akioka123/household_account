"""create month_notes table

Revision ID: 008
Revises: 007
Create Date: 2024-01-01 00:00:00.000002

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'month_notes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('year_month', sa.String(length=7), nullable=False),
        sa.Column('note', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('year_month', name='uq_month_notes_year_month'),
    )
    op.create_index('ix_month_notes_year_month', 'month_notes', ['year_month'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_month_notes_year_month', table_name='month_notes')
    op.drop_table('month_notes')
