"""
Test Suite for Celery Background Tasks
Tests task execution, retry logic, error handling, and logging
"""

import pytest
import logging
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.celery_config import celery_app
from app.tasks import (
    fetch_stock_prices_task,
    fetch_news_task,
    health_check,
    get_tracked_stocks,
    get_db_session,
)
from app.models import Stock
from app.exceptions import (
    APIError,
    NetworkError,
    DatabaseError,
    RateLimitError,
    InvalidTickerError,
)


# Configure Celery to use synchronous execution for testing
celery_app.conf.update(
    task_always_eager=True,
    task_eager_propagates=True,
)


class TestGetTrackedStocks:
    """Test suite for get_tracked_stocks helper function"""

    def test_get_tracked_stocks_success(self):
        """Test successful retrieval of tracked stocks"""
        # Mock database session and stocks
        mock_db = MagicMock(spec=Session)
        mock_stocks = [
            Mock(id=1, ticker="AAPL", company_name="Apple Inc."),
            Mock(id=2, ticker="GOOGL", company_name="Alphabet Inc."),
        ]
        mock_db.query.return_value.all.return_value = mock_stocks

        # Call function
        result = get_tracked_stocks(mock_db)

        # Assertions
        assert len(result) == 2
        assert result[0]["ticker"] == "AAPL"
        assert result[1]["ticker"] == "GOOGL"
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2

    def test_get_tracked_stocks_empty(self):
        """Test when no stocks are found"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.all.return_value = []

        result = get_tracked_stocks(mock_db)

        assert result == []

    def test_get_tracked_stocks_database_error(self):
        """Test error handling when database query fails"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.side_effect = Exception("Database connection failed")

        with pytest.raises(DatabaseError):
            get_tracked_stocks(mock_db)


class TestFetchStockPricesTask:
    """Test suite for fetch_stock_prices_task"""

    @patch("app.tasks.get_db_session")
    @patch("app.tasks.get_tracked_stocks")
    @patch("app.tasks.YahooFinanceFetcher")
    def test_fetch_stock_prices_success(self, mock_fetcher_class, mock_get_stocks, mock_get_db):
        """Test successful stock price fetch"""
        # Setup mocks
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db

        stocks = [
            {"id": 1, "ticker": "AAPL", "name": "Apple Inc."},
            {"id": 2, "ticker": "GOOGL", "name": "Alphabet Inc."},
        ]
        mock_get_stocks.return_value = stocks

        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.fetch_and_save_multiple.return_value = {
            "AAPL": (100, 20),  # inserted, updated
            "GOOGL": (95, 15),
        }

        # Call task
        result = fetch_stock_prices_task()

        # Assertions
        assert result["status"] == "success"
        assert result["fetched"] == 2
        assert result["stored"] == 195  # 100 + 95
        assert result["errors"] == 0
        mock_db.close.assert_called()

    @patch("app.tasks.get_db_session")
    @patch("app.tasks.get_tracked_stocks")
    def test_fetch_stock_prices_no_stocks(self, mock_get_stocks, mock_get_db):
        """Test when no stocks are found"""
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_get_stocks.return_value = []

        result = fetch_stock_prices_task()

        assert result["status"] == "success"
        assert result["fetched"] == 0
        assert result["stored"] == 0
        assert result["message"] == "No stocks found"

    @patch("app.tasks.get_db_session")
    @patch("app.tasks.get_tracked_stocks")
    @patch("app.tasks.YahooFinanceFetcher")
    def test_fetch_stock_prices_partial_failure(
        self, mock_fetcher_class, mock_get_stocks, mock_get_db
    ):
        """Test when some stocks fail to fetch"""
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db

        stocks = [
            {"id": 1, "ticker": "AAPL", "name": "Apple Inc."},
            {"id": 2, "ticker": "INVALID", "name": "Invalid Corp"},
        ]
        mock_get_stocks.return_value = stocks

        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.fetch_and_save_multiple.return_value = {
            "AAPL": (100, 20),
            "INVALID": (0, 0),  # Failed
        }

        result = fetch_stock_prices_task()

        assert result["status"] == "success"
        assert result["fetched"] == 1
        assert result["errors"] == 1

    @patch("app.tasks.get_db_session")
    @patch("app.tasks.get_tracked_stocks")
    def test_fetch_stock_prices_network_error_retry(self, mock_get_stocks, mock_get_db):
        """Test retry on network error"""
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_get_stocks.side_effect = NetworkError("Connection failed")

        # Create a task instance with mock retry method
        task = fetch_stock_prices_task

        with patch.object(task, "retry") as mock_retry:
            mock_retry.side_effect = NetworkError("Connection failed")

            with pytest.raises(NetworkError):
                task()

    @patch("app.tasks.get_db_session")
    def test_fetch_stock_prices_db_cleanup_on_error(self, mock_get_db):
        """Test that database connection is closed even on error"""
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db

        with patch("app.tasks.get_tracked_stocks", side_effect=Exception("Test error")):
            result = fetch_stock_prices_task()

            assert result["status"] == "failed"
            mock_db.close.assert_called()


class TestFetchNewsTask:
    """Test suite for fetch_news_task"""

    @patch("app.tasks.get_db_session")
    @patch("app.tasks.get_tracked_stocks")
    @patch("app.tasks.NewsAPIFetcher")
    def test_fetch_news_success(self, mock_fetcher_class, mock_get_stocks, mock_get_db):
        """Test successful news fetch"""
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db

        stocks = [
            {"id": 1, "ticker": "AAPL", "name": "Apple Inc."},
            {"id": 2, "ticker": "GOOGL", "name": "Alphabet Inc."},
        ]
        mock_get_stocks.return_value = stocks

        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.fetch_and_save_multiple.return_value = {
            "AAPL": (50, 5),  # inserted, duplicates
            "GOOGL": (45, 3),
        }

        result = fetch_news_task()

        assert result["status"] == "success"
        assert result["fetched"] == 2
        assert result["stored"] == 95  # 50 + 45
        assert result["duplicates"] == 8  # 5 + 3
        mock_db.close.assert_called()

    @patch("app.tasks.get_db_session")
    @patch("app.tasks.get_tracked_stocks")
    def test_fetch_news_no_stocks(self, mock_get_stocks, mock_get_db):
        """Test when no stocks are found"""
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_get_stocks.return_value = []

        result = fetch_news_task()

        assert result["status"] == "success"
        assert result["fetched"] == 0
        assert result["stored"] == 0
        assert result["message"] == "No stocks found"

    @patch("app.tasks.get_db_session")
    @patch("app.tasks.get_tracked_stocks")
    @patch("app.tasks.NewsAPIFetcher")
    def test_fetch_news_rate_limit_error(
        self, mock_fetcher_class, mock_get_stocks, mock_get_db
    ):
        """Test rate limit handling"""
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db

        stocks = [{"id": 1, "ticker": "AAPL", "name": "Apple Inc."}]
        mock_get_stocks.return_value = stocks

        # Mock fetcher to raise RateLimitError
        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.fetch_and_save_multiple.side_effect = RateLimitError(
            "Daily quota exceeded"
        )

        task = fetch_news_task

        with patch.object(task, "retry") as mock_retry:
            mock_retry.side_effect = RateLimitError("Daily quota exceeded")

            with pytest.raises(RateLimitError):
                task()

    @patch("app.tasks.get_db_session")
    @patch("app.tasks.get_tracked_stocks")
    @patch("app.tasks.NewsAPIFetcher")
    def test_fetch_news_network_error_retry(
        self, mock_fetcher_class, mock_get_stocks, mock_get_db
    ):
        """Test retry on network error"""
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db

        stocks = [{"id": 1, "ticker": "AAPL", "name": "Apple Inc."}]
        mock_get_stocks.return_value = stocks

        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.fetch_and_save_multiple.side_effect = NetworkError(
            "Connection timeout"
        )

        task = fetch_news_task

        with patch.object(task, "retry") as mock_retry:
            mock_retry.side_effect = NetworkError("Connection timeout")

            with pytest.raises(NetworkError):
                task()

    @patch("app.tasks.get_db_session")
    def test_fetch_news_db_cleanup_on_error(self, mock_get_db):
        """Test that database connection is closed even on error"""
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db

        with patch("app.tasks.get_tracked_stocks", side_effect=Exception("Test error")):
            result = fetch_news_task()

            assert result["status"] == "failed"
            mock_db.close.assert_called()


class TestHealthCheck:
    """Test suite for health_check task"""

    @patch("app.tasks.get_db_session")
    def test_health_check_success(self, mock_get_db):
        """Test successful health check"""
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db

        mock_query = MagicMock()
        mock_query.count.return_value = 5
        mock_db.query.return_value = mock_query

        result = health_check()

        assert result["status"] == "healthy"
        assert result["stocks_in_db"] == 5
        assert "timestamp" in result
        mock_db.close.assert_called()

    @patch("app.tasks.get_db_session")
    def test_health_check_database_error(self, mock_get_db):
        """Test health check when database is unavailable"""
        mock_get_db.side_effect = Exception("Database connection failed")

        result = health_check()

        assert result["status"] == "unhealthy"
        assert "error" in result
        assert "Database connection failed" in result["error"]

    @patch("app.tasks.get_db_session")
    def test_health_check_query_error(self, mock_get_db):
        """Test health check when database query fails"""
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_db.query.side_effect = Exception("Query failed")

        result = health_check()

        assert result["status"] == "unhealthy"
        assert "error" in result


class TestTaskIdempotency:
    """Test suite for task idempotency (safe to retry)"""

    @patch("app.tasks.get_db_session")
    @patch("app.tasks.get_tracked_stocks")
    @patch("app.tasks.YahooFinanceFetcher")
    def test_stock_price_task_idempotent(
        self, mock_fetcher_class, mock_get_stocks, mock_get_db
    ):
        """
        Test that fetching prices twice with same data
        doesn't cause issues (idempotent operation)
        """
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db

        stocks = [{"id": 1, "ticker": "AAPL", "name": "Apple Inc."}]
        mock_get_stocks.return_value = stocks

        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        # First call returns fresh data
        mock_fetcher.fetch_and_save_multiple.return_value = {"AAPL": (100, 0)}

        result1 = fetch_stock_prices_task()
        assert result1["status"] == "success"

        # Reset mock and simulate second execution
        mock_fetcher.reset_mock()
        # Second call returns updated counts (some records updated, not inserted)
        mock_fetcher.fetch_and_save_multiple.return_value = {"AAPL": (0, 100)}

        result2 = fetch_stock_prices_task()
        assert result2["status"] == "success"

        # Both results indicate success but with different insert/update counts
        # This is expected behavior - task is idempotent


class TestTaskConfiguration:
    """Test suite for task configuration"""

    def test_fetch_stock_prices_task_registered(self):
        """Test that fetch_stock_prices_task is registered with Celery"""
        assert "app.tasks.fetch_stock_prices_task" in celery_app.tasks

    def test_fetch_news_task_registered(self):
        """Test that fetch_news_task is registered with Celery"""
        assert "app.tasks.fetch_news_task" in celery_app.tasks

    def test_health_check_task_registered(self):
        """Test that health_check task is registered with Celery"""
        assert "app.tasks.health_check" in celery_app.tasks

    def test_celery_app_configuration(self):
        """Test Celery app configuration"""
        # Check broker URL is set
        assert celery_app.conf.broker_url

        # Check result backend is set
        assert celery_app.conf.result_backend

        # Check task serializer is JSON
        assert celery_app.conf.task_serializer == "json"

        # Check accept_content includes JSON
        assert "json" in celery_app.conf.accept_content

        # Check task routing is configured
        assert "task_routes" in celery_app.conf


class TestTaskErrorHandling:
    """Test suite for error handling and logging"""

    @patch("app.tasks.logger")
    @patch("app.tasks.get_db_session")
    @patch("app.tasks.get_tracked_stocks")
    def test_task_logs_start_and_completion(
        self, mock_get_stocks, mock_get_db, mock_logger
    ):
        """Test that tasks log start and completion"""
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db
        mock_get_stocks.return_value = []

        fetch_stock_prices_task()

        # Check logging calls
        assert mock_logger.info.called
        # Get all info log calls as strings
        log_calls = [call.args if call.args else str(call.kwargs) for call in mock_logger.info.call_args_list]
        # Convert to strings for checking
        log_strings = [str(msg).lower() for msg in log_calls]
        # Should have logging for task start
        assert any("starting" in msg for msg in log_strings)

    @patch("app.tasks.get_db_session")
    def test_task_handles_db_close_error(self, mock_get_db):
        """Test that task handles errors when closing database"""
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db
        # Raise error on close
        mock_db.close.side_effect = Exception("Close failed")

        with patch("app.tasks.get_tracked_stocks", return_value=[]):
            # Should not raise, should handle close error gracefully
            result = fetch_stock_prices_task()
            assert result["status"] == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
