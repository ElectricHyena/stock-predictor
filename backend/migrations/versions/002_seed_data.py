"""Seed migration - add initial stocks data

Revision ID: 002
Revises: 001
Create Date: 2026-01-03

This migration seeds the database with initial stock data for common
stocks used in testing and development.
"""

from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add initial stock seed data"""

    # Insert initial stocks
    stocks_table = sa.table(
        'stocks',
        sa.column('ticker', sa.String),
        sa.column('company_name', sa.String),
        sa.column('market', sa.String),
        sa.column('sector', sa.String),
        sa.column('industry', sa.String),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )

    now = datetime.utcnow()

    op.bulk_insert(
        stocks_table,
        [
            {
                'ticker': 'AAPL',
                'company_name': 'Apple Inc.',
                'market': 'NYSE',
                'sector': 'Technology',
                'industry': 'Consumer Electronics',
                'created_at': now,
                'updated_at': now,
            },
            {
                'ticker': 'GOOGL',
                'company_name': 'Alphabet Inc.',
                'market': 'NASDAQ',
                'sector': 'Technology',
                'industry': 'Internet Services',
                'created_at': now,
                'updated_at': now,
            },
            {
                'ticker': 'MSFT',
                'company_name': 'Microsoft Corporation',
                'market': 'NASDAQ',
                'sector': 'Technology',
                'industry': 'Software',
                'created_at': now,
                'updated_at': now,
            },
            {
                'ticker': 'AMZN',
                'company_name': 'Amazon.com Inc.',
                'market': 'NASDAQ',
                'sector': 'Consumer Cyclical',
                'industry': 'Internet Retail',
                'created_at': now,
                'updated_at': now,
            },
            {
                'ticker': 'TSLA',
                'company_name': 'Tesla Inc.',
                'market': 'NASDAQ',
                'sector': 'Consumer Cyclical',
                'industry': 'Automobiles',
                'created_at': now,
                'updated_at': now,
            },
        ]
    )


def downgrade() -> None:
    """Remove seeded stocks"""

    op.execute(
        sa.delete(sa.table('stocks')).where(
            sa.table('stocks').c.ticker.in_(['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'])
        )
    )
