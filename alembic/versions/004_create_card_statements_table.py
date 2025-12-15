"""create card_statements table

Revision ID: 004
Revises: 003
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'card_statements',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('year_month', sa.String(length=7), nullable=False),
        sa.Column('card_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['card_id'], ['cards.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('year_month', 'card_id', name='uq_card_statements_year_month_card')
    )
    
    op.create_index('ix_card_statements_year_month', 'card_statements', ['year_month'], unique=False)
    op.create_index('ix_card_statements_card_id', 'card_statements', ['card_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_card_statements_card_id', table_name='card_statements')
    op.drop_index('ix_card_statements_year_month', table_name='card_statements')
    op.drop_table('card_statements')
