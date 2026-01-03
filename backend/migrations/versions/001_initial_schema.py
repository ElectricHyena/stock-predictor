"""Initial migration - create all database tables

Revision ID: 001
Revises:
Create Date: 2026-01-03

This migration creates all 8 core tables for the Stock Predictor application:
- users: User accounts
- stocks: Stock master data
- stock_prices: Historical OHLCV data
- news_events: News and events
- event_categories: Event category classifications
- sentiment_scores: Sentiment analysis results
- event_price_correlations: Event-price correlations
- predictability_scores: Predictability metrics

All tables include proper foreign key constraints, cascading deletes,
and indexes on frequently queried columns.
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
    """Create all required database tables"""

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Create stocks table
    op.create_table(
        'stocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticker', sa.String(length=20), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('market', sa.String(length=10), nullable=False),
        sa.Column('sector', sa.String(length=100), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('last_price_updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_news_updated_at', sa.DateTime(), nullable=True),
        sa.Column('analysis_status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_stocks_id', 'stocks', ['id'], unique=False)
    op.create_index('ix_stocks_ticker', 'stocks', ['ticker'], unique=True)
    op.create_index('ix_stocks_market', 'stocks', ['market'], unique=False)

    # Create stock_prices table
    op.create_table(
        'stock_prices',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('open_price', sa.Float(), nullable=True),
        sa.Column('high_price', sa.Float(), nullable=True),
        sa.Column('low_price', sa.Float(), nullable=True),
        sa.Column('close_price', sa.Float(), nullable=True),
        sa.Column('volume', sa.BigInteger(), nullable=True),
        sa.Column('adjusted_close', sa.Float(), nullable=True),
        sa.Column('daily_return_pct', sa.Float(), nullable=True),
        sa.Column('price_range', sa.Float(), nullable=True),
        sa.Column('is_valid', sa.Boolean(), nullable=True),
        sa.Column('data_source', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stock_id', 'date', name='uq_stock_date')
    )
    op.create_index('ix_stock_prices_id', 'stock_prices', ['id'], unique=False)
    op.create_index('ix_stock_prices_stock_id', 'stock_prices', ['stock_id'], unique=False)
    op.create_index('ix_stock_prices_date', 'stock_prices', ['date'], unique=False)

    # Create news_events table
    op.create_table(
        'news_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('headline', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('event_category', sa.String(length=50), nullable=False),
        sa.Column('event_subcategory', sa.String(length=50), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('sentiment_category', sa.String(length=20), nullable=True),
        sa.Column('source_name', sa.String(length=100), nullable=True),
        sa.Column('source_quality', sa.Float(), nullable=True),
        sa.Column('original_url', sa.String(length=500), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('is_duplicate', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_news_events_id', 'news_events', ['id'], unique=False)
    op.create_index('ix_news_events_stock_id', 'news_events', ['stock_id'], unique=False)
    op.create_index('ix_news_events_event_date', 'news_events', ['event_date'], unique=False)
    op.create_index('ix_news_events_event_category', 'news_events', ['event_category'], unique=False)
    op.create_index('ix_news_events_content_hash', 'news_events', ['content_hash'], unique=False)

    # Create event_categories table
    op.create_table(
        'event_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['news_events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_event_categories_id', 'event_categories', ['id'], unique=False)
    op.create_index('ix_event_categories_event_id', 'event_categories', ['event_id'], unique=False)
    op.create_index('ix_event_categories_category', 'event_categories', ['category'], unique=False)

    # Create sentiment_scores table
    op.create_table(
        'sentiment_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['news_events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sentiment_scores_id', 'sentiment_scores', ['id'], unique=False)
    op.create_index('ix_sentiment_scores_event_id', 'sentiment_scores', ['event_id'], unique=False)

    # Create event_price_correlations table
    op.create_table(
        'event_price_correlations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('news_event_id', sa.Integer(), nullable=True),
        sa.Column('event_category', sa.String(length=50), nullable=False),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('price_change_pct', sa.Float(), nullable=True),
        sa.Column('price_direction', sa.String(length=5), nullable=True),
        sa.Column('price_magnitude', sa.Float(), nullable=True),
        sa.Column('days_to_move', sa.Integer(), nullable=True),
        sa.Column('is_immediate', sa.Boolean(), nullable=True),
        sa.Column('historical_win_rate', sa.Float(), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['news_event_id'], ['news_events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_event_price_correlations_id', 'event_price_correlations', ['id'], unique=False)
    op.create_index('ix_event_price_correlations_stock_id', 'event_price_correlations', ['stock_id'], unique=False)

    # Create predictability_scores table
    op.create_table(
        'predictability_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('information_availability_score', sa.Integer(), nullable=True),
        sa.Column('pattern_consistency_score', sa.Integer(), nullable=True),
        sa.Column('timing_certainty_score', sa.Integer(), nullable=True),
        sa.Column('direction_confidence_score', sa.Integer(), nullable=True),
        sa.Column('overall_predictability_score', sa.Integer(), nullable=True),
        sa.Column('current_events', sa.JSON(), nullable=True),
        sa.Column('prediction_direction', sa.String(length=5), nullable=True),
        sa.Column('prediction_magnitude_low', sa.Float(), nullable=True),
        sa.Column('prediction_magnitude_high', sa.Float(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_predictability_scores_id', 'predictability_scores', ['id'], unique=False)
    op.create_index('ix_predictability_scores_stock_id', 'predictability_scores', ['stock_id'], unique=False)


def downgrade() -> None:
    """Drop all database tables"""

    # Drop indices
    op.drop_index('ix_predictability_scores_stock_id', table_name='predictability_scores')
    op.drop_index('ix_predictability_scores_id', table_name='predictability_scores')
    op.drop_index('ix_event_price_correlations_stock_id', table_name='event_price_correlations')
    op.drop_index('ix_event_price_correlations_id', table_name='event_price_correlations')
    op.drop_index('ix_sentiment_scores_event_id', table_name='sentiment_scores')
    op.drop_index('ix_sentiment_scores_id', table_name='sentiment_scores')
    op.drop_index('ix_event_categories_category', table_name='event_categories')
    op.drop_index('ix_event_categories_event_id', table_name='event_categories')
    op.drop_index('ix_event_categories_id', table_name='event_categories')
    op.drop_index('ix_news_events_content_hash', table_name='news_events')
    op.drop_index('ix_news_events_event_category', table_name='news_events')
    op.drop_index('ix_news_events_event_date', table_name='news_events')
    op.drop_index('ix_news_events_stock_id', table_name='news_events')
    op.drop_index('ix_news_events_id', table_name='news_events')
    op.drop_index('ix_stock_prices_date', table_name='stock_prices')
    op.drop_index('ix_stock_prices_stock_id', table_name='stock_prices')
    op.drop_index('ix_stock_prices_id', table_name='stock_prices')
    op.drop_index('ix_stocks_market', table_name='stocks')
    op.drop_index('ix_stocks_ticker', table_name='stocks')
    op.drop_index('ix_stocks_id', table_name='stocks')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_id', table_name='users')

    # Drop tables in reverse order of dependencies
    op.drop_table('predictability_scores')
    op.drop_table('event_price_correlations')
    op.drop_table('sentiment_scores')
    op.drop_table('event_categories')
    op.drop_table('news_events')
    op.drop_table('stock_prices')
    op.drop_table('stocks')
    op.drop_table('users')
