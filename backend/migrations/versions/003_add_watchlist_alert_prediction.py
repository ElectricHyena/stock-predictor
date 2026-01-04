"""Add watchlist, alert, and prediction tables

Revision ID: 003
Revises: 002
Create Date: 2026-01-03

This migration adds:
- watchlists: User watchlist collections
- watchlist_items: Individual stocks in watchlists
- alerts: User price and prediction alerts
- alert_triggers: Alert trigger history
- predictions: Stock price predictions
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create watchlist, alert, and prediction tables"""

    # Create watchlists table
    op.create_table(
        'watchlists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_default', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_watchlists_id', 'watchlists', ['id'], unique=False)
    op.create_index('ix_watchlists_user_id', 'watchlists', ['user_id'], unique=False)

    # Create watchlist_items table
    op.create_table(
        'watchlist_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('watchlist_id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('tags', sa.String(length=500), nullable=True),
        sa.Column('added_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['watchlist_id'], ['watchlists.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('watchlist_id', 'stock_id', name='uq_watchlist_stock')
    )
    op.create_index('ix_watchlist_items_id', 'watchlist_items', ['id'], unique=False)
    op.create_index('ix_watchlist_items_watchlist_id', 'watchlist_items', ['watchlist_id'], unique=False)
    op.create_index('ix_watchlist_items_stock_id', 'watchlist_items', ['stock_id'], unique=False)

    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('condition_value', sa.Float(), nullable=False),
        sa.Column('condition_operator', sa.String(length=10), nullable=True, default='>='),
        sa.Column('frequency', sa.String(length=20), nullable=True, default='realtime'),
        sa.Column('status', sa.String(length=20), nullable=True, default='active'),
        sa.Column('is_enabled', sa.Integer(), nullable=True, default=1),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('notify_email', sa.Integer(), nullable=True, default=1),
        sa.Column('notify_push', sa.Integer(), nullable=True, default=0),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alerts_id', 'alerts', ['id'], unique=False)
    op.create_index('ix_alerts_user_id', 'alerts', ['user_id'], unique=False)
    op.create_index('ix_alerts_stock_id', 'alerts', ['stock_id'], unique=False)
    op.create_index('ix_alerts_status', 'alerts', ['status'], unique=False)

    # Create alert_triggers table
    op.create_table(
        'alert_triggers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('triggered_value', sa.Float(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('is_read', sa.Integer(), nullable=True, default=0),
        sa.Column('is_dismissed', sa.Integer(), nullable=True, default=0),
        sa.Column('notified_via', sa.String(length=50), nullable=True),
        sa.Column('triggered_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['alert_id'], ['alerts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alert_triggers_id', 'alert_triggers', ['id'], unique=False)
    op.create_index('ix_alert_triggers_alert_id', 'alert_triggers', ['alert_id'], unique=False)
    op.create_index('ix_alert_triggers_triggered_at', 'alert_triggers', ['triggered_at'], unique=False)

    # Create predictions table
    op.create_table(
        'predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('direction', sa.String(length=10), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('timing', sa.String(length=20), nullable=True),
        sa.Column('expected_move_min', sa.Float(), nullable=True),
        sa.Column('expected_move_max', sa.Float(), nullable=True),
        sa.Column('historical_win_rate', sa.Float(), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('prediction_date', sa.Date(), nullable=False),
        sa.Column('target_date', sa.Date(), nullable=True),
        sa.Column('actual_move', sa.Float(), nullable=True),
        sa.Column('was_correct', sa.Boolean(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_predictions_id', 'predictions', ['id'], unique=False)
    op.create_index('ix_predictions_stock_id', 'predictions', ['stock_id'], unique=False)
    op.create_index('ix_predictions_prediction_date', 'predictions', ['prediction_date'], unique=False)
    op.create_index('ix_predictions_is_current', 'predictions', ['is_current'], unique=False)


def downgrade() -> None:
    """Drop watchlist, alert, and prediction tables"""

    # Drop indices
    op.drop_index('ix_predictions_is_current', table_name='predictions')
    op.drop_index('ix_predictions_prediction_date', table_name='predictions')
    op.drop_index('ix_predictions_stock_id', table_name='predictions')
    op.drop_index('ix_predictions_id', table_name='predictions')

    op.drop_index('ix_alert_triggers_triggered_at', table_name='alert_triggers')
    op.drop_index('ix_alert_triggers_alert_id', table_name='alert_triggers')
    op.drop_index('ix_alert_triggers_id', table_name='alert_triggers')

    op.drop_index('ix_alerts_status', table_name='alerts')
    op.drop_index('ix_alerts_stock_id', table_name='alerts')
    op.drop_index('ix_alerts_user_id', table_name='alerts')
    op.drop_index('ix_alerts_id', table_name='alerts')

    op.drop_index('ix_watchlist_items_stock_id', table_name='watchlist_items')
    op.drop_index('ix_watchlist_items_watchlist_id', table_name='watchlist_items')
    op.drop_index('ix_watchlist_items_id', table_name='watchlist_items')

    op.drop_index('ix_watchlists_user_id', table_name='watchlists')
    op.drop_index('ix_watchlists_id', table_name='watchlists')

    # Drop tables in reverse order of dependencies
    op.drop_table('predictions')
    op.drop_table('alert_triggers')
    op.drop_table('alerts')
    op.drop_table('watchlist_items')
    op.drop_table('watchlists')
