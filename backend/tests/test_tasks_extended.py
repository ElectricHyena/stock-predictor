"""
Extended Tests for Celery Background Tasks
Covers additional task functionality: backtest, correlations, alerts, signal handlers
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from app.celery_config import celery_app
from app.tasks import (
    run_backtest_task,
    regenerate_correlations_task,
    check_alerts_task,
    dead_letter_handler,
    task_prerun_handler,
    task_postrun_handler,
    task_retry_handler,
    task_failure_handler,
)
from app.models import Alert, AlertTrigger, AlertType, AlertStatus, Stock, StockPrice


# Configure Celery for testing
celery_app.conf.update(
    task_always_eager=True,
    task_eager_propagates=True,
)


class TestRunBacktestTask:
    """Tests for run_backtest_task - these are functional tests that mock the task binding"""

    def test_run_backtest_task_registered(self):
        """Test run_backtest_task is registered"""
        # Verify the task is in registered tasks
        assert "app.tasks.run_backtest_task" in celery_app.tasks

    def test_run_backtest_task_has_correct_config(self):
        """Test backtest task has correct configuration"""
        task = celery_app.tasks["app.tasks.run_backtest_task"]
        assert task.max_retries == 2
        assert task.default_retry_delay == 30


class TestRegenerateCorrelationsTask:
    """Tests for regenerate_correlations_task"""

    @patch("app.tasks.get_db_session")
    @patch("app.tasks.get_tracked_stocks")
    def test_regenerate_correlations_success(self, mock_get_stocks, mock_get_db):
        """Test successful correlation regeneration"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        stocks = [
            {"id": 1, "ticker": "AAPL", "name": "Apple Inc."},
            {"id": 2, "ticker": "GOOGL", "name": "Alphabet Inc."},
        ]
        mock_get_stocks.return_value = stocks

        # Mock the query for deleting old correlations
        mock_delete_query = MagicMock()
        mock_delete_query.delete.return_value = 5
        mock_db.query.return_value.filter.return_value = mock_delete_query

        result = regenerate_correlations_task()

        assert result["status"] == "success"
        assert result["stocks_processed"] == 2
        mock_db.commit.assert_called()
        mock_db.close.assert_called()

    @patch("app.tasks.get_db_session")
    @patch("app.tasks.get_tracked_stocks")
    def test_regenerate_correlations_no_stocks(self, mock_get_stocks, mock_get_db):
        """Test correlation regeneration with no stocks"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_stocks.return_value = []

        result = regenerate_correlations_task()

        assert result["status"] == "success"
        assert result["stocks_processed"] == 0

    @patch("app.tasks.get_db_session")
    @patch("app.tasks.get_tracked_stocks")
    def test_regenerate_correlations_error(self, mock_get_stocks, mock_get_db):
        """Test correlation regeneration error handling"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_stocks.side_effect = Exception("Database error")

        result = regenerate_correlations_task()

        assert result["status"] == "failed"
        assert "error" in result


class TestCheckAlertsTask:
    """Tests for check_alerts_task"""

    @patch("app.tasks.get_db_session")
    def test_check_alerts_no_active_alerts(self, mock_get_db):
        """Test alert check with no active alerts"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # No active alerts
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = check_alerts_task()

        assert result["status"] == "success"
        assert result["alerts_checked"] == 0
        assert result["alerts_triggered"] == 0

    @patch("app.tasks.get_db_session")
    def test_check_alerts_price_above_triggered(self, mock_get_db):
        """Test alert triggered when price goes above threshold"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Create mock alert
        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_alert.stock_id = 1
        mock_alert.alert_type = AlertType.PRICE_ABOVE
        mock_alert.condition_value = 150.0
        mock_alert.condition_operator = ">="
        mock_alert.triggers = []

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_alert]

        # Mock latest price above threshold
        mock_price = MagicMock()
        mock_price.close_price = 155.0
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_price

        result = check_alerts_task()

        assert result["status"] == "success"
        assert result["alerts_checked"] == 1
        assert result["alerts_triggered"] == 1
        mock_db.commit.assert_called()

    @patch("app.tasks.get_db_session")
    def test_check_alerts_price_below_triggered(self, mock_get_db):
        """Test alert triggered when price goes below threshold"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_alert = MagicMock()
        mock_alert.id = 2
        mock_alert.stock_id = 1
        mock_alert.alert_type = AlertType.PRICE_BELOW
        mock_alert.condition_value = 100.0
        mock_alert.condition_operator = "<="
        mock_alert.triggers = []

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_alert]

        mock_price = MagicMock()
        mock_price.close_price = 95.0
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_price

        result = check_alerts_task()

        assert result["status"] == "success"
        assert result["alerts_triggered"] == 1

    @patch("app.tasks.get_db_session")
    def test_check_alerts_not_triggered(self, mock_get_db):
        """Test alert not triggered when condition not met"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_alert = MagicMock()
        mock_alert.id = 3
        mock_alert.stock_id = 1
        mock_alert.alert_type = AlertType.PRICE_ABOVE
        mock_alert.condition_value = 200.0
        mock_alert.condition_operator = ">="
        mock_alert.triggers = []

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_alert]

        mock_price = MagicMock()
        mock_price.close_price = 150.0  # Below threshold
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_price

        result = check_alerts_task()

        assert result["status"] == "success"
        assert result["alerts_checked"] == 1
        assert result["alerts_triggered"] == 0

    @patch("app.tasks.get_db_session")
    def test_check_alerts_no_price_data(self, mock_get_db):
        """Test alert check when no price data available"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_alert = MagicMock()
        mock_alert.id = 4
        mock_alert.stock_id = 1
        mock_alert.alert_type = AlertType.PRICE_ABOVE
        mock_alert.condition_value = 150.0
        mock_alert.condition_operator = ">="
        mock_alert.triggers = []

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_alert]
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = check_alerts_task()

        assert result["status"] == "success"
        assert result["alerts_triggered"] == 0

    @patch("app.tasks.get_db_session")
    def test_check_alerts_error_handling(self, mock_get_db):
        """Test alert check error handling"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.side_effect = Exception("Database error")

        result = check_alerts_task()

        assert result["status"] == "failed"
        assert "error" in result


class TestDeadLetterHandler:
    """Tests for dead_letter_handler task"""

    def test_dead_letter_handler_logs_failure(self):
        """Test dead letter handler logs failed task info"""
        failed_task_info = {
            "task_id": "abc123",
            "task_name": "app.tasks.fetch_stock_prices_task",
            "args": "('AAPL',)",
            "kwargs": "{}",
            "exception_type": "NetworkError",
            "exception_message": "Connection timeout",
            "traceback": "Traceback...",
            "failed_at": "2024-01-01T12:00:00",
        }

        result = dead_letter_handler(failed_task_info)

        assert result["status"] == "logged"
        assert result["task_id"] == "abc123"
        assert result["task_name"] == "app.tasks.fetch_stock_prices_task"
        assert "handled_at" in result

    def test_dead_letter_handler_missing_info(self):
        """Test dead letter handler with missing info"""
        failed_task_info = {}

        result = dead_letter_handler(failed_task_info)

        assert result["status"] == "logged"
        assert result["task_id"] == "unknown"
        assert result["task_name"] == "unknown"


class TestCelerySignalHandlers:
    """Tests for Celery signal handlers"""

    def test_task_prerun_handler(self):
        """Test task prerun handler records start time"""
        from app.tasks import _task_start_times

        mock_task = MagicMock()
        mock_task.name = "test_task"

        # Clear any existing entries
        _task_start_times.clear()

        task_prerun_handler(task_id="test123", task=mock_task)

        assert "test123" in _task_start_times
        assert isinstance(_task_start_times["test123"], float)

    def test_task_postrun_handler_success(self):
        """Test task postrun handler records metrics"""
        from app.tasks import _task_start_times

        mock_task = MagicMock()
        mock_task.name = "test_task"

        # Set up start time
        _task_start_times["test456"] = 1000.0

        with patch("app.tasks.time.time", return_value=1005.0):
            with patch("app.tasks.metrics") as mock_metrics:
                task_postrun_handler(
                    task_id="test456",
                    task=mock_task,
                    retval={"status": "success"},
                    state="SUCCESS"
                )

                mock_metrics.record_celery_task.assert_called()

    def test_task_retry_handler(self):
        """Test task retry handler records retry metrics"""
        mock_request = MagicMock()
        mock_request.task = "test_task"
        mock_request.id = "retry123"

        with patch("app.tasks.metrics") as mock_metrics:
            task_retry_handler(
                request=mock_request,
                reason="Connection error",
                einfo=None
            )

            mock_metrics.record_celery_retry.assert_called_with("test_task")

    def test_task_failure_handler(self):
        """Test task failure handler records failure metrics"""
        mock_sender = MagicMock()
        mock_sender.name = "failed_task"

        exception = ValueError("Test error")

        with patch("app.tasks.metrics") as mock_metrics:
            with patch("app.tasks.celery_app.send_task"):
                task_failure_handler(
                    task_id="fail123",
                    exception=exception,
                    args=(),
                    kwargs={},
                    traceback=None,
                    einfo=None,
                    sender=mock_sender
                )

                mock_metrics.record_celery_task.assert_called()
                mock_metrics.record_dead_letter.assert_called()


class TestTaskRegistration:
    """Tests for task registration"""

    def test_run_backtest_task_registered(self):
        """Test run_backtest_task is registered"""
        assert "app.tasks.run_backtest_task" in celery_app.tasks

    def test_regenerate_correlations_task_registered(self):
        """Test regenerate_correlations_task is registered"""
        assert "app.tasks.regenerate_correlations_task" in celery_app.tasks

    def test_check_alerts_task_registered(self):
        """Test check_alerts_task is registered"""
        assert "app.tasks.check_alerts_task" in celery_app.tasks

    def test_dead_letter_handler_registered(self):
        """Test dead_letter_handler is registered"""
        assert "app.tasks.dead_letter_handler" in celery_app.tasks
