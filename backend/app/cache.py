"""
Redis Caching Utilities
Provides caching decorator and cache management for API endpoints
"""

import redis
import json
import logging
from functools import wraps
from typing import Callable, Any, Optional
from datetime import datetime, timedelta
from app.config import settings

logger = logging.getLogger(__name__)

# Redis client
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


class RedisCache:
    """Redis cache manager for API responses"""

    def __init__(self, redis_url: str = settings.REDIS_URL):
        """Initialize Redis client"""
        self.client = redis.from_url(redis_url, decode_responses=True)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in cache with TTL"""
        try:
            # Use default=str to handle datetime and other non-JSON-serializable types
            json_value = json.dumps(value, default=str)
            self.client.setex(key, ttl_seconds, json_value)
            logger.debug(f"Cached key {key} with TTL {ttl_seconds}s")
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            # Don't raise - just log and continue without caching

    def delete(self, key: str):
        """Delete value from cache"""
        try:
            self.client.delete(key)
            logger.debug(f"Deleted cache key {key}")
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")

    def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
                logger.debug(f"Cleared {len(keys)} cache keys matching {pattern}")
        except Exception as e:
            logger.error(f"Cache clear error for pattern {pattern}: {e}")

    def clear(self):
        """Clear all cache keys (useful for testing)"""
        try:
            self.client.flushdb()
            logger.debug("Cleared all cache keys")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")


# Global cache instance
cache = RedisCache()


def cached(ttl_seconds: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results in Redis

    Args:
        ttl_seconds: Time to live for cache in seconds
        key_prefix: Optional prefix for cache key

    Usage:
        @cached(ttl_seconds=300, key_prefix="stocks")
        async def get_stock_data(ticker: str):
            return {"ticker": ticker}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # Build cache key
            key_parts = [key_prefix] if key_prefix else [func.__name__]
            key_parts.extend(str(arg) for arg in args if isinstance(arg, (str, int, float)))
            key_parts.extend(f"{k}={v}" for k, v in kwargs.items() if isinstance(v, (str, int, float)))
            cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for key {cache_key}")
                return cached_value

            # Call function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # Build cache key
            key_parts = [key_prefix] if key_prefix else [func.__name__]
            key_parts.extend(str(arg) for arg in args if isinstance(arg, (str, int, float)))
            key_parts.extend(f"{k}={v}" for k, v in kwargs.items() if isinstance(v, (str, int, float)))
            cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for key {cache_key}")
                return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds)
            return result

        # Return async or sync wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Cache TTL constants (in seconds)
CACHE_TTL_SEARCH = 5 * 60  # 5 minutes for search results
CACHE_TTL_DETAIL = 10 * 60  # 10 minutes for stock details
CACHE_TTL_PREDICTABILITY = 30 * 60  # 30 minutes for predictability scores
CACHE_TTL_PREDICTION = 60 * 60  # 1 hour for predictions
CACHE_TTL_ANALYSIS = 60 * 60  # 1 hour for historical analysis
CACHE_TTL_BACKTEST = 60 * 60  # 1 hour for backtest results


# Cache key patterns
def cache_key_search(query: str, market: Optional[str] = None) -> str:
    """Generate cache key for stock search"""
    parts = ["search", query.lower()]
    if market:
        parts.append(market.upper())
    return ":".join(parts)


def cache_key_detail(ticker: str) -> str:
    """Generate cache key for stock detail"""
    return f"detail:{ticker.upper()}"


def cache_key_predictability(ticker: str) -> str:
    """Generate cache key for predictability score"""
    return f"predictability:{ticker.upper()}"


def cache_key_prediction(ticker: str) -> str:
    """Generate cache key for price prediction"""
    return f"prediction:{ticker.upper()}"


def cache_key_analysis(ticker: str, period: str = "1y") -> str:
    """Generate cache key for historical analysis"""
    return f"analysis:{ticker.upper()}:{period}"


def cache_key_backtest(ticker: str, strategy_name: str) -> str:
    """Generate cache key for backtest results"""
    return f"backtest:{ticker.upper()}:{strategy_name.lower()}"
