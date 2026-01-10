"""Add is_active column to stocks table

Revision ID: 006
Revises: 005
Create Date: 2026-01-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    """Add is_active column to stocks table with default True"""
    op.add_column(
        'stocks',
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True)
    )

    # Set default value for existing rows
    op.execute("UPDATE stocks SET is_active = TRUE WHERE is_active IS NULL")

    # Create index for efficient filtering
    op.create_index('ix_stocks_is_active', 'stocks', ['is_active'])


def downgrade():
    """Remove is_active column from stocks table"""
    op.drop_index('ix_stocks_is_active', table_name='stocks')
    op.drop_column('stocks', 'is_active')
