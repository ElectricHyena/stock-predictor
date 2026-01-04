"""
Rate Limiting Implementation
"""
import time
import os
import redis
from functools import wraps
from typing import Tuple, Optional
from fastapi import Request, HTTPException, status

from app.config import settings
from app.exceptions import RateLimitError

# Configuration from settings or environment
REDIS_URL = getattr(settings, 'REDIS_URL', os.getenv('REDIS_URL', 'redis://localhost:6379'))
RATE_LIMITING_ENABLED = os.getenv('RATE_LIMITING_ENABLED', 'false').lower() == 'true'


class RateLimiter:
    """Rate limiting implementation using Redis"""

    # Rate limit tiers (requests per hour)
    RATE_LIMITS = {
        "auth": 30,           # Auth endpoints: 30/hour
        "search": 100,        # Search: 100/hour
        "data": 200,          # Data retrieval: 200/hour
        "prediction": 150,    # Predictions: 150/hour
        "watchlist": 100,     # Watchlist operations: 100/hour
        "default": 100        # Default: 100/hour
    }

    def __init__(self):
        self.enabled = RATE_LIMITING_ENABLED
        if self.enabled:
            try:
                self.redis_client = redis.from_url(REDIS_URL)
                self.redis_client.ping()
            except Exception as e:
                print(f"Warning: Redis connection failed for rate limiting: {e}")
                self.enabled = False
        self.memory_store = {}

    def get_client_id(self, request: Request, user_id: Optional[str] = None) -> str:
        """Get unique client identifier"""
        if user_id:
            return f"user:{user_id}"
        else:
            client_ip = request.client.host if request.client else "unknown"
            return f"ip:{client_ip}"

    def is_rate_limited(
        self,
        client_id: str,
        endpoint: str,
        tier: str = "default"
    ) -> Tuple[bool, int, int]:
        """
        Check if client has exceeded rate limit

        Returns: (is_limited: bool, remaining: int, reset_at: int)
        """
        if not self.enabled:
            return False, -1, 0

        limit = self.RATE_LIMITS.get(tier, self.RATE_LIMITS["default"])
        window = 3600  # 1 hour in seconds

        key = f"rate_limit:{client_id}:{endpoint}"

        if self.enabled and self.redis_client:
            return self._check_redis_limit(key, limit, window)
        else:
            return self._check_memory_limit(key, limit, window)

    def _check_redis_limit(self, key: str, limit: int, window: int) -> Tuple[bool, int, int]:
        """Check rate limit using Redis"""
        try:
            current = self.redis_client.incr(key)

            if current == 1:
                self.redis_client.expire(key, window)

            ttl = self.redis_client.ttl(key)
            remaining = max(0, limit - current)
            reset_at = int(time.time()) + ttl

            is_limited = current > limit

            return is_limited, remaining, reset_at
        except Exception as e:
            print(f"Redis rate limit check failed: {e}")
            return False, -1, 0

    def _check_memory_limit(self, key: str, limit: int, window: int) -> Tuple[bool, int, int]:
        """Check rate limit using memory (development only)"""
        now = time.time()

        if key not in self.memory_store:
            self.memory_store[key] = {
                'count': 0,
                'window_start': now,
                'expiration': now + window
            }

        record = self.memory_store[key]

        # Check if window has expired
        if now > record['expiration']:
            record['count'] = 0
            record['window_start'] = now
            record['expiration'] = now + window

        record['count'] += 1
        remaining = max(0, limit - record['count'])
        reset_at = int(record['expiration'])

        is_limited = record['count'] > limit

        return is_limited, remaining, reset_at

    def reset_client_limit(self, client_id: str, endpoint: str):
        """Reset rate limit for a client"""
        if not self.enabled:
            return

        key = f"rate_limit:{client_id}:{endpoint}"

        if self.redis_client:
            self.redis_client.delete(key)
        else:
            self.memory_store.pop(key, None)


def rate_limit(tier: str = "default"):
    """Decorator for rate limiting endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            if not RATE_LIMITING_ENABLED:
                return await func(request, *args, **kwargs)

            limiter = RateLimiter()

            # Get client identifier
            user_id = getattr(request.state, "user_id", None)
            client_id = limiter.get_client_id(request, user_id)

            # Check rate limit
            is_limited, remaining, reset_at = limiter.is_rate_limited(
                client_id,
                request.url.path,
                tier
            )

            if is_limited:
                raise RateLimitError(
                    f"Rate limit exceeded for {tier} tier",
                    limiter.RATE_LIMITS[tier]
                )

            # Call the function
            response = await func(request, *args, **kwargs)

            # Add rate limit headers
            if hasattr(response, "headers"):
                response.headers["X-RateLimit-Limit"] = str(limiter.RATE_LIMITS[tier])
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Reset"] = str(reset_at)

            return response

        return wrapper
    return decorator
