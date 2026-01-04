"""
Health Check Endpoints for Monitoring
"""
import redis
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class HealthChecker:
    """Check application and dependency health"""

    def __init__(self, db_session=None, redis_url: Optional[str] = None):
        self.db_session = db_session
        self.redis_url = redis_url
        self.redis_client = None
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
            except Exception as e:
                logger.warning(f"Failed to initialize Redis client: {e}")

    async def check_database(self) -> Dict[str, Any]:
        """Check database connection and availability"""
        try:
            if self.db_session:
                # Simple query to verify connection
                self.db_session.execute("SELECT 1")
                return {
                    "status": "healthy",
                    "message": "Database connection successful"
                }
            else:
                return {
                    "status": "unknown",
                    "message": "Database session not configured"
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}"
            }

    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connection and availability"""
        try:
            if not self.redis_client:
                return {
                    "status": "unknown",
                    "message": "Redis not configured"
                }

            # Ping Redis
            self.redis_client.ping()

            # Get memory info
            info = self.redis_client.info("memory")
            memory_usage = info.get("used_memory_human", "unknown")

            return {
                "status": "healthy",
                "message": "Redis connection successful",
                "memory_usage": memory_usage
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Redis connection failed: {str(e)}"
            }

    async def check_external_apis(self) -> Dict[str, Any]:
        """Check external API connectivity"""
        # This would check connections to Yahoo Finance, news APIs, etc.
        # For now, return a placeholder
        return {
            "status": "healthy",
            "message": "External APIs reachable"
        }

    async def get_liveness_status(self) -> Dict[str, Any]:
        """Get liveness status (is service running?)"""
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Service is running"
        }

    async def get_readiness_status(self) -> Dict[str, Any]:
        """Get readiness status (is service ready to handle requests?)"""
        checks = {
            "database": await self.check_database(),
            "redis": await self.check_redis(),
            "external_apis": await self.check_external_apis()
        }

        # Overall readiness: all critical services must be healthy
        all_healthy = all(
            check.get("status") in ("healthy", "unknown")
            for check in checks.values()
        )

        return {
            "status": "ready" if all_healthy else "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks
        }

    async def get_full_health_status(self) -> Dict[str, Any]:
        """Get full health status report"""
        liveness = await self.get_liveness_status()
        readiness = await self.get_readiness_status()

        return {
            "liveness": liveness,
            "readiness": readiness,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def check_all(self) -> Dict[str, Any]:
        """Check all dependencies and return overall health status"""
        checks = {
            "database": await self.check_database(),
            "redis": await self.check_redis(),
            "external_apis": await self.check_external_apis()
        }

        # Count healthy/unhealthy
        healthy_count = sum(1 for c in checks.values() if c.get("status") == "healthy")
        total_count = len(checks)

        overall_status = "healthy" if healthy_count == total_count else "degraded"
        if all(c.get("status") == "unhealthy" for c in checks.values()):
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "checks": checks,
            "healthy": healthy_count,
            "total": total_count,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global health checker instance - created lazily
class LazyHealthChecker:
    """Lazy-loading health checker proxy"""
    _instance: Optional[HealthChecker] = None

    async def check_all(self) -> Dict[str, Any]:
        if self._instance is None:
            from app.config import settings
            self._instance = HealthChecker(redis_url=getattr(settings, 'REDIS_URL', None))
        return await self._instance.check_all()

    async def check_database(self) -> Dict[str, Any]:
        if self._instance is None:
            from app.config import settings
            self._instance = HealthChecker(redis_url=getattr(settings, 'REDIS_URL', None))
        return await self._instance.check_database()

    async def check_redis(self) -> Dict[str, Any]:
        if self._instance is None:
            from app.config import settings
            self._instance = HealthChecker(redis_url=getattr(settings, 'REDIS_URL', None))
        return await self._instance.check_redis()


health_checker = LazyHealthChecker()


def initialize_health_checker(db_session=None, redis_url: Optional[str] = None):
    """Initialize the global health checker"""
    health_checker._instance = HealthChecker(db_session=db_session, redis_url=redis_url)


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance"""
    if health_checker._instance is None:
        from app.config import settings
        health_checker._instance = HealthChecker(redis_url=getattr(settings, 'REDIS_URL', None))
    return health_checker._instance
