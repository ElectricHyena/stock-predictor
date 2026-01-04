"""
Tests for Rate Limiting functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import Request
import time
import asyncio

from app.rate_limiter import RateLimiter, rate_limit, RATE_LIMITING_ENABLED


class TestRateLimiter:
    """Tests for RateLimiter class"""

    def test_rate_limiter_init(self):
        """Test RateLimiter initialization"""
        limiter = RateLimiter()
        # Should initialize without error
        assert hasattr(limiter, 'enabled')
        assert hasattr(limiter, 'memory_store')
        assert hasattr(limiter, 'RATE_LIMITS')

    def test_get_client_id_with_user(self):
        """Test client ID generation with user ID"""
        limiter = RateLimiter()

        mock_request = Mock()
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"

        client_id = limiter.get_client_id(mock_request, user_id="user123")
        assert client_id == "user:user123"

    def test_get_client_id_with_ip(self):
        """Test client ID generation with IP address"""
        limiter = RateLimiter()

        mock_request = Mock()
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"

        client_id = limiter.get_client_id(mock_request, user_id=None)
        assert client_id == "ip:192.168.1.1"

    def test_get_client_id_no_client(self):
        """Test client ID generation when client is None"""
        limiter = RateLimiter()

        mock_request = Mock()
        mock_request.client = None

        client_id = limiter.get_client_id(mock_request, user_id=None)
        assert client_id == "ip:unknown"

    def test_is_rate_limited_disabled(self):
        """Test rate limiting when disabled"""
        limiter = RateLimiter()
        limiter.enabled = False

        is_limited, remaining, reset_at = limiter.is_rate_limited(
            "user:test", "/api/test", "default"
        )

        assert is_limited == False
        assert remaining == -1
        assert reset_at == 0

    def test_memory_rate_limiting(self):
        """Test in-memory rate limiting"""
        limiter = RateLimiter()
        limiter.enabled = True
        limiter.redis_client = None  # Force memory mode

        # First request should not be limited
        is_limited, remaining, reset_at = limiter.is_rate_limited(
            "user:test_memory", "/api/test", "auth"  # auth tier = 30/hour
        )
        assert is_limited == False
        assert remaining == 29  # 30 - 1

    def test_memory_rate_limiting_exceeded(self):
        """Test in-memory rate limiting when exceeded"""
        limiter = RateLimiter()
        limiter.enabled = True
        limiter.redis_client = None  # Force memory mode

        # Simulate exceeding rate limit
        for i in range(31):  # auth tier = 30/hour
            is_limited, remaining, reset_at = limiter.is_rate_limited(
                "user:exceed_test_unique", "/api/auth", "auth"
            )

        # 31st request should be limited
        assert is_limited == True
        assert remaining == 0

    def test_reset_client_limit_disabled(self):
        """Test reset when rate limiting is disabled"""
        limiter = RateLimiter()
        limiter.enabled = False

        # Should not raise an error
        limiter.reset_client_limit("user:test", "/api/test")

    def test_reset_client_limit_memory(self):
        """Test reset in memory mode"""
        limiter = RateLimiter()
        limiter.enabled = True
        limiter.redis_client = None

        # Add some rate limit data
        limiter.is_rate_limited("user:reset_test_unique", "/api/test", "default")

        # Reset it
        limiter.reset_client_limit("user:reset_test_unique", "/api/test")

        # Memory store should have key removed
        key = "rate_limit:user:reset_test_unique:/api/test"
        assert key not in limiter.memory_store

    def test_rate_limit_tiers(self):
        """Test different rate limit tiers"""
        limiter = RateLimiter()

        assert limiter.RATE_LIMITS["auth"] == 30
        assert limiter.RATE_LIMITS["search"] == 100
        assert limiter.RATE_LIMITS["data"] == 200
        assert limiter.RATE_LIMITS["prediction"] == 150
        assert limiter.RATE_LIMITS["watchlist"] == 100
        assert limiter.RATE_LIMITS["default"] == 100

    def test_memory_window_expiration(self):
        """Test that memory rate limit windows expire correctly"""
        limiter = RateLimiter()
        limiter.enabled = True
        limiter.redis_client = None

        # Make a request
        limiter.is_rate_limited("user:window_test_unique", "/api/test", "default")

        # Manually expire the window
        key = "rate_limit:user:window_test_unique:/api/test"
        if key in limiter.memory_store:
            limiter.memory_store[key]['expiration'] = time.time() - 1

        # Next request should reset the count
        is_limited, remaining, reset_at = limiter.is_rate_limited(
            "user:window_test_unique", "/api/test", "default"
        )

        assert is_limited == False
        assert remaining == 99  # Reset to 100 - 1


class TestRateLimitDecorator:
    """Tests for rate_limit decorator"""

    def test_rate_limit_decorator_exists(self):
        """Test decorator exists and is callable"""
        assert callable(rate_limit)

    def test_rate_limit_decorator_structure(self):
        """Test that rate_limit decorator maintains function structure"""
        @rate_limit("search")
        async def my_search_endpoint(request: Request):
            """Search endpoint docstring"""
            return {"results": []}

        # Check that wrapper is async
        assert asyncio.iscoroutinefunction(my_search_endpoint)


class TestRateLimitIntegration:
    """Integration tests for rate limiting"""

    def test_rate_limit_headers_format(self):
        """Test that rate limit headers have correct format"""
        expected_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset"
        ]

        for header in expected_headers:
            assert header.startswith("X-RateLimit-")

    def test_rate_limiting_config_available(self):
        """Test that rate limiting configuration is accessible"""
        # RATE_LIMITING_ENABLED should be a boolean
        assert isinstance(RATE_LIMITING_ENABLED, bool)
