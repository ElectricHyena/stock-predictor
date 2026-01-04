"""
Tests for Logging Configuration
"""
import pytest
import logging
import json
import tempfile
import os
from pathlib import Path

from app.logging_config import JSONFormatter, configure_logging, get_logger


class TestJSONFormatter:
    """Tests for JSONFormatter class"""

    def test_format_basic_record(self):
        """Test formatting a basic log record"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["logger"] == "test_logger"
        assert data["message"] == "Test message"
        assert data["line"] == 42
        assert "timestamp" in data

    def test_format_with_request_id(self):
        """Test formatting record with request_id extra"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=10,
            msg="Request processed",
            args=(),
            exc_info=None
        )
        record.request_id = "abc123"

        output = formatter.format(record)
        data = json.loads(output)

        assert data["request_id"] == "abc123"

    def test_format_with_user_id(self):
        """Test formatting record with user_id extra"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=10,
            msg="User action",
            args=(),
            exc_info=None
        )
        record.user_id = "user_456"

        output = formatter.format(record)
        data = json.loads(output)

        assert data["user_id"] == "user_456"

    def test_format_with_endpoint(self):
        """Test formatting record with endpoint extra"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=10,
            msg="Endpoint hit",
            args=(),
            exc_info=None
        )
        record.endpoint = "/api/stocks"

        output = formatter.format(record)
        data = json.loads(output)

        assert data["endpoint"] == "/api/stocks"

    def test_format_with_method(self):
        """Test formatting record with HTTP method extra"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=10,
            msg="HTTP request",
            args=(),
            exc_info=None
        )
        record.method = "GET"

        output = formatter.format(record)
        data = json.loads(output)

        assert data["method"] == "GET"

    def test_format_with_status_code(self):
        """Test formatting record with status_code extra"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=10,
            msg="Response sent",
            args=(),
            exc_info=None
        )
        record.status_code = 200

        output = formatter.format(record)
        data = json.loads(output)

        assert data["status_code"] == 200

    def test_format_with_response_time(self):
        """Test formatting record with response_time_ms extra"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=10,
            msg="Request completed",
            args=(),
            exc_info=None
        )
        record.response_time_ms = 150.5

        output = formatter.format(record)
        data = json.loads(output)

        assert data["response_time_ms"] == 150.5

    def test_format_with_exception(self):
        """Test formatting record with exception info"""
        formatter = JSONFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="/test/path.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert "exception" in data
        assert "ValueError" in data["exception"]

    def test_format_with_all_extras(self):
        """Test formatting record with all extra fields"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=10,
            msg="Full request",
            args=(),
            exc_info=None
        )
        record.request_id = "req_123"
        record.user_id = "user_456"
        record.endpoint = "/api/test"
        record.method = "POST"
        record.status_code = 201
        record.response_time_ms = 100

        output = formatter.format(record)
        data = json.loads(output)

        assert data["request_id"] == "req_123"
        assert data["user_id"] == "user_456"
        assert data["endpoint"] == "/api/test"
        assert data["method"] == "POST"
        assert data["status_code"] == 201
        assert data["response_time_ms"] == 100


class TestConfigureLogging:
    """Tests for configure_logging function"""

    def test_configure_logging_creates_log_dir(self):
        """Test that configure_logging creates log directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = os.path.join(tmpdir, "test_logs")
            configure_logging(log_level="INFO", log_dir=log_dir)
            assert Path(log_dir).exists()

    def test_configure_logging_returns_logger(self):
        """Test that configure_logging returns root logger"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = os.path.join(tmpdir, "test_logs")
            logger = configure_logging(log_level="INFO", log_dir=log_dir)
            assert isinstance(logger, logging.Logger)

    def test_configure_logging_sets_level(self):
        """Test that configure_logging sets correct log level"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = os.path.join(tmpdir, "test_logs")
            logger = configure_logging(log_level="DEBUG", log_dir=log_dir)
            assert logger.level == logging.DEBUG

    def test_configure_logging_invalid_level(self):
        """Test configure_logging with invalid log level defaults to INFO"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = os.path.join(tmpdir, "test_logs")
            logger = configure_logging(log_level="INVALID", log_dir=log_dir)
            assert logger.level == logging.INFO

    def test_configure_logging_adds_handlers(self):
        """Test that configure_logging adds handlers"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = os.path.join(tmpdir, "test_logs")
            logger = configure_logging(log_level="INFO", log_dir=log_dir)
            # Should have file handlers and console handler
            assert len(logger.handlers) >= 2


class TestGetLogger:
    """Tests for get_logger function"""

    def test_get_logger_returns_logger(self):
        """Test get_logger returns a logger instance"""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_same_name_same_logger(self):
        """Test get_logger returns same logger for same name"""
        logger1 = get_logger("shared_module")
        logger2 = get_logger("shared_module")
        assert logger1 is logger2

    def test_get_logger_different_names(self):
        """Test get_logger returns different loggers for different names"""
        logger1 = get_logger("module_a")
        logger2 = get_logger("module_b")
        assert logger1 is not logger2
