"""
Tests for Redis Caching Utilities
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock

from app.cache import (
    RedisCache,
    cache,
    cached,
    cache_key_search,
    cache_key_detail,
    cache_key_predictability,
    cache_key_prediction,
    cache_key_analysis,
    cache_key_backtest,
    CACHE_TTL_SEARCH,
    CACHE_TTL_DETAIL,
    CACHE_TTL_PREDICTABILITY,
    CACHE_TTL_PREDICTION,
    CACHE_TTL_ANALYSIS,
    CACHE_TTL_BACKTEST,
)


class TestRedisCacheClass:
    """Tests for RedisCache class"""

    def test_redis_cache_init(self):
        """Test RedisCache initialization"""
        with patch('app.cache.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_redis.return_value = mock_client
            cache_instance = RedisCache("redis://localhost:6379")
            assert cache_instance.client == mock_client

    def test_cache_get_success(self):
        """Test cache get returns cached value"""
        with patch('app.cache.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.get.return_value = '{"key": "value"}'
            mock_redis.return_value = mock_client

            cache_instance = RedisCache()
            result = cache_instance.get("test_key")

            assert result == {"key": "value"}
            mock_client.get.assert_called_once_with("test_key")

    def test_cache_get_miss(self):
        """Test cache get returns None on miss"""
        with patch('app.cache.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.get.return_value = None
            mock_redis.return_value = mock_client

            cache_instance = RedisCache()
            result = cache_instance.get("missing_key")

            assert result is None

    def test_cache_get_error(self):
        """Test cache get handles errors gracefully"""
        with patch('app.cache.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.get.side_effect = Exception("Connection error")
            mock_redis.return_value = mock_client

            cache_instance = RedisCache()
            result = cache_instance.get("error_key")

            assert result is None

    def test_cache_set_success(self):
        """Test cache set stores value"""
        with patch('app.cache.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_redis.return_value = mock_client

            cache_instance = RedisCache()
            cache_instance.set("test_key", {"data": "value"}, ttl_seconds=300)

            mock_client.setex.assert_called_once()
            args = mock_client.setex.call_args[0]
            assert args[0] == "test_key"
            assert args[1] == 300

    def test_cache_set_error(self):
        """Test cache set handles errors gracefully"""
        with patch('app.cache.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.setex.side_effect = Exception("Connection error")
            mock_redis.return_value = mock_client

            cache_instance = RedisCache()
            # Should not raise
            cache_instance.set("test_key", {"data": "value"})

    def test_cache_delete_success(self):
        """Test cache delete removes key"""
        with patch('app.cache.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_redis.return_value = mock_client

            cache_instance = RedisCache()
            cache_instance.delete("test_key")

            mock_client.delete.assert_called_once_with("test_key")

    def test_cache_delete_error(self):
        """Test cache delete handles errors gracefully"""
        with patch('app.cache.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.delete.side_effect = Exception("Connection error")
            mock_redis.return_value = mock_client

            cache_instance = RedisCache()
            # Should not raise
            cache_instance.delete("test_key")

    def test_cache_clear_pattern_success(self):
        """Test cache clear_pattern removes matching keys"""
        with patch('app.cache.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.keys.return_value = ["key:1", "key:2", "key:3"]
            mock_redis.return_value = mock_client

            cache_instance = RedisCache()
            cache_instance.clear_pattern("key:*")

            mock_client.keys.assert_called_once_with("key:*")
            mock_client.delete.assert_called_once_with("key:1", "key:2", "key:3")

    def test_cache_clear_pattern_no_keys(self):
        """Test cache clear_pattern with no matching keys"""
        with patch('app.cache.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.keys.return_value = []
            mock_redis.return_value = mock_client

            cache_instance = RedisCache()
            cache_instance.clear_pattern("nonexistent:*")

            mock_client.keys.assert_called_once_with("nonexistent:*")
            mock_client.delete.assert_not_called()

    def test_cache_clear_pattern_error(self):
        """Test cache clear_pattern handles errors"""
        with patch('app.cache.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.keys.side_effect = Exception("Connection error")
            mock_redis.return_value = mock_client

            cache_instance = RedisCache()
            # Should not raise
            cache_instance.clear_pattern("error:*")


class TestCachedDecorator:
    """Tests for cached decorator"""

    @pytest.mark.asyncio
    async def test_cached_async_miss(self):
        """Test cached decorator with cache miss (async)"""
        with patch.object(cache, 'get', return_value=None):
            with patch.object(cache, 'set') as mock_set:
                @cached(ttl_seconds=300, key_prefix="test")
                async def async_func(arg1: str):
                    return {"result": arg1}

                result = await async_func("value1")

                assert result == {"result": "value1"}
                mock_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_cached_async_hit(self):
        """Test cached decorator with cache hit (async)"""
        with patch.object(cache, 'get', return_value={"cached": True}):
            @cached(ttl_seconds=300, key_prefix="test")
            async def async_func(arg1: str):
                return {"result": arg1}

            result = await async_func("value1")

            assert result == {"cached": True}

    def test_cached_sync_miss(self):
        """Test cached decorator with cache miss (sync)"""
        with patch.object(cache, 'get', return_value=None):
            with patch.object(cache, 'set') as mock_set:
                @cached(ttl_seconds=300, key_prefix="test")
                def sync_func(arg1: str):
                    return {"result": arg1}

                result = sync_func("value1")

                assert result == {"result": "value1"}
                mock_set.assert_called_once()

    def test_cached_sync_hit(self):
        """Test cached decorator with cache hit (sync)"""
        with patch.object(cache, 'get', return_value={"cached": True}):
            @cached(ttl_seconds=300, key_prefix="test")
            def sync_func(arg1: str):
                return {"result": arg1}

            result = sync_func("value1")

            assert result == {"cached": True}

    def test_cached_without_prefix(self):
        """Test cached decorator without key prefix"""
        with patch.object(cache, 'get', return_value=None):
            with patch.object(cache, 'set') as mock_set:
                @cached(ttl_seconds=300)
                def my_function(arg1: str):
                    return {"result": arg1}

                result = my_function("test")

                assert result == {"result": "test"}

    def test_cached_with_kwargs(self):
        """Test cached decorator with keyword arguments"""
        with patch.object(cache, 'get', return_value=None):
            with patch.object(cache, 'set') as mock_set:
                @cached(ttl_seconds=300, key_prefix="test")
                def func_with_kwargs(name: str, count: int = 10):
                    return {"name": name, "count": count}

                result = func_with_kwargs("test", count=5)

                assert result == {"name": "test", "count": 5}


class TestCacheKeyFunctions:
    """Tests for cache key generation functions"""

    def test_cache_key_search_basic(self):
        """Test cache key generation for search"""
        key = cache_key_search("AAPL")
        assert key == "search:aapl"

    def test_cache_key_search_with_market(self):
        """Test cache key generation for search with market"""
        key = cache_key_search("AAPL", market="NYSE")
        assert key == "search:aapl:NYSE"

    def test_cache_key_detail(self):
        """Test cache key generation for stock detail"""
        key = cache_key_detail("AAPL")
        assert key == "detail:AAPL"

    def test_cache_key_detail_lowercase(self):
        """Test cache key detail converts to uppercase"""
        key = cache_key_detail("aapl")
        assert key == "detail:AAPL"

    def test_cache_key_predictability(self):
        """Test cache key generation for predictability"""
        key = cache_key_predictability("GOOGL")
        assert key == "predictability:GOOGL"

    def test_cache_key_prediction(self):
        """Test cache key generation for prediction"""
        key = cache_key_prediction("MSFT")
        assert key == "prediction:MSFT"

    def test_cache_key_analysis_default(self):
        """Test cache key generation for analysis with default period"""
        key = cache_key_analysis("AMZN")
        assert key == "analysis:AMZN:1y"

    def test_cache_key_analysis_custom_period(self):
        """Test cache key generation for analysis with custom period"""
        key = cache_key_analysis("AMZN", period="6m")
        assert key == "analysis:AMZN:6m"

    def test_cache_key_backtest(self):
        """Test cache key generation for backtest"""
        key = cache_key_backtest("TSLA", "Momentum Strategy")
        assert key == "backtest:TSLA:momentum strategy"


class TestCacheTTLConstants:
    """Tests for cache TTL constants"""

    def test_cache_ttl_search(self):
        """Test search cache TTL is 5 minutes"""
        assert CACHE_TTL_SEARCH == 5 * 60

    def test_cache_ttl_detail(self):
        """Test detail cache TTL is 10 minutes"""
        assert CACHE_TTL_DETAIL == 10 * 60

    def test_cache_ttl_predictability(self):
        """Test predictability cache TTL is 30 minutes"""
        assert CACHE_TTL_PREDICTABILITY == 30 * 60

    def test_cache_ttl_prediction(self):
        """Test prediction cache TTL is 1 hour"""
        assert CACHE_TTL_PREDICTION == 60 * 60

    def test_cache_ttl_analysis(self):
        """Test analysis cache TTL is 1 hour"""
        assert CACHE_TTL_ANALYSIS == 60 * 60

    def test_cache_ttl_backtest(self):
        """Test backtest cache TTL is 1 hour"""
        assert CACHE_TTL_BACKTEST == 60 * 60


class TestGlobalCacheInstance:
    """Tests for the global cache instance"""

    def test_global_cache_exists(self):
        """Test that global cache instance exists"""
        assert cache is not None
        assert isinstance(cache, RedisCache)
