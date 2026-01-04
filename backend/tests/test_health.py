"""Health Check Tests"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app


def test_health_check():
    """Test health check endpoint"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_endpoint():
    """Test root endpoint"""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


def test_liveness_probe():
    """Test liveness probe endpoint"""
    client = TestClient(app)
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_metrics_endpoint():
    """Test Prometheus metrics endpoint"""
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")


class TestHealthChecker:
    """Tests for HealthChecker class"""

    @pytest.mark.asyncio
    async def test_check_database_success(self):
        """Test database health check success"""
        from app.health import HealthChecker

        mock_session = Mock()
        mock_session.execute = Mock(return_value=None)

        checker = HealthChecker(db_session=mock_session)
        result = await checker.check_database()

        assert result["status"] == "healthy"
        assert "connection successful" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_check_database_no_session(self):
        """Test database health check without session"""
        from app.health import HealthChecker

        checker = HealthChecker(db_session=None)
        result = await checker.check_database()

        assert result["status"] == "unknown"
        assert "not configured" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_check_database_failure(self):
        """Test database health check failure"""
        from app.health import HealthChecker

        mock_session = Mock()
        mock_session.execute = Mock(side_effect=Exception("Connection refused"))

        checker = HealthChecker(db_session=mock_session)
        result = await checker.check_database()

        assert result["status"] == "unhealthy"
        assert "failed" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_check_redis_not_configured(self):
        """Test Redis health check when not configured"""
        from app.health import HealthChecker

        checker = HealthChecker(redis_url=None)
        result = await checker.check_redis()

        assert result["status"] == "unknown"
        assert "not configured" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_check_external_apis(self):
        """Test external APIs health check"""
        from app.health import HealthChecker

        checker = HealthChecker()
        result = await checker.check_external_apis()

        assert result["status"] == "healthy"
        assert "reachable" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_get_liveness_status(self):
        """Test liveness status"""
        from app.health import HealthChecker

        checker = HealthChecker()
        result = await checker.get_liveness_status()

        assert result["status"] == "alive"
        assert "timestamp" in result
        assert "running" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_get_readiness_status_ready(self):
        """Test readiness status when all healthy"""
        from app.health import HealthChecker

        checker = HealthChecker()

        # Mock all checks to return healthy
        checker.check_database = AsyncMock(return_value={"status": "healthy", "message": "ok"})
        checker.check_redis = AsyncMock(return_value={"status": "healthy", "message": "ok"})
        checker.check_external_apis = AsyncMock(return_value={"status": "healthy", "message": "ok"})

        result = await checker.get_readiness_status()

        assert result["status"] == "ready"
        assert "checks" in result

    @pytest.mark.asyncio
    async def test_get_readiness_status_not_ready(self):
        """Test readiness status when unhealthy"""
        from app.health import HealthChecker

        checker = HealthChecker()

        # Mock database to return unhealthy
        checker.check_database = AsyncMock(return_value={"status": "unhealthy", "message": "failed"})
        checker.check_redis = AsyncMock(return_value={"status": "healthy", "message": "ok"})
        checker.check_external_apis = AsyncMock(return_value={"status": "healthy", "message": "ok"})

        result = await checker.get_readiness_status()

        assert result["status"] == "not_ready"

    @pytest.mark.asyncio
    async def test_get_full_health_status(self):
        """Test full health status report"""
        from app.health import HealthChecker

        checker = HealthChecker()
        checker.check_database = AsyncMock(return_value={"status": "healthy", "message": "ok"})
        checker.check_redis = AsyncMock(return_value={"status": "healthy", "message": "ok"})
        checker.check_external_apis = AsyncMock(return_value={"status": "healthy", "message": "ok"})

        result = await checker.get_full_health_status()

        assert "liveness" in result
        assert "readiness" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_check_all(self):
        """Test check_all method"""
        from app.health import HealthChecker

        checker = HealthChecker()
        checker.check_database = AsyncMock(return_value={"status": "healthy", "message": "ok"})
        checker.check_redis = AsyncMock(return_value={"status": "healthy", "message": "ok"})
        checker.check_external_apis = AsyncMock(return_value={"status": "healthy", "message": "ok"})

        result = await checker.check_all()

        assert result["status"] == "healthy"
        assert result["healthy"] == 3
        assert result["total"] == 3
        assert "checks" in result

    @pytest.mark.asyncio
    async def test_check_all_degraded(self):
        """Test check_all when some checks fail"""
        from app.health import HealthChecker

        checker = HealthChecker()
        checker.check_database = AsyncMock(return_value={"status": "unhealthy", "message": "failed"})
        checker.check_redis = AsyncMock(return_value={"status": "healthy", "message": "ok"})
        checker.check_external_apis = AsyncMock(return_value={"status": "healthy", "message": "ok"})

        result = await checker.check_all()

        assert result["status"] == "degraded"
        assert result["healthy"] == 2
        assert result["total"] == 3


class TestHealthCheckHelpers:
    """Tests for health check helper functions"""

    def test_get_health_checker(self):
        """Test get_health_checker function"""
        from app.health import get_health_checker, HealthChecker

        with patch('app.config.settings') as mock_settings:
            mock_settings.REDIS_URL = None
            checker = get_health_checker()

            assert isinstance(checker, HealthChecker)
