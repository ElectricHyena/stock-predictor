"""Add updated_at columns to missing tables

Revision ID: 004
Revises: 003
Create Date: 2026-01-03

This migration adds updated_at columns to:
- predictability_scores
- event_categories
- sentiment_scores
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
    """Add updated_at columns to tables missing them"""

    # Add updated_at to predictability_scores
    op.add_column(
        'predictability_scores',
        sa.Column('updated_at', sa.DateTime(), nullable=True)
    )

    # Add updated_at to event_categories
    op.add_column(
        'event_categories',
        sa.Column('updated_at', sa.DateTime(), nullable=True)
    )

    # Add updated_at to sentiment_scores
    op.add_column(
        'sentiment_scores',
        sa.Column('updated_at', sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    """Remove updated_at columns"""

    op.drop_column('sentiment_scores', 'updated_at')
    op.drop_column('event_categories', 'updated_at')
    op.drop_column('predictability_scores', 'updated_at')
