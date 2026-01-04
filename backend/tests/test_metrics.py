"""
Tests for Prometheus Metrics Collection
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock

from app.metrics import (
    MetricsCollector,
    metrics,
    track_request_metrics,
    track_prediction_metrics,
    track_db_query,
    PROMETHEUS_AVAILABLE
)


class TestMetricsCollector:
    """Tests for MetricsCollector class"""

    def test_metrics_collector_init(self):
        """Test MetricsCollector initialization"""
        collector = MetricsCollector()
        if PROMETHEUS_AVAILABLE:
            assert hasattr(collector, 'registry')
            assert hasattr(collector, 'http_requests')
        else:
            assert hasattr(collector, 'metrics_data')

    def test_record_http_request(self):
        """Test recording HTTP request metrics"""
        collector = MetricsCollector()
        # Should not raise
        collector.record_http_request("GET", "/api/stocks", 200, 0.05)
        collector.record_http_request("POST", "/api/stocks", 201, 0.1)
        collector.record_http_request("GET", "/api/stocks", 500, 0.02)

    def test_record_api_error(self):
        """Test recording API errors"""
        collector = MetricsCollector()
        collector.record_api_error("/api/stocks", "NOT_FOUND")
        collector.record_api_error("/api/stocks", "VALIDATION_ERROR")

    def test_record_prediction(self):
        """Test recording prediction metrics"""
        collector = MetricsCollector()
        collector.record_prediction("event_correlation", 0.5)
        collector.record_prediction("sentiment", 0.3)

    def test_record_cache_hit(self):
        """Test recording cache hits"""
        collector = MetricsCollector()
        collector.record_cache_hit("redis")
        collector.record_cache_hit("memory")

    def test_record_cache_miss(self):
        """Test recording cache misses"""
        collector = MetricsCollector()
        collector.record_cache_miss("redis")
        collector.record_cache_miss("memory")

    def test_record_db_query(self):
        """Test recording database query metrics"""
        collector = MetricsCollector()
        collector.record_db_query("SELECT", 0.01)
        collector.record_db_query("INSERT", 0.02)
        collector.record_db_query("UPDATE", 0.015)

    def test_record_stock_analyzed(self):
        """Test recording stock analyzed metric"""
        collector = MetricsCollector()
        collector.record_stock_analyzed()
        collector.record_stock_analyzed()

    def test_record_backtest_run(self):
        """Test recording backtest run metric"""
        collector = MetricsCollector()
        collector.record_backtest_run("momentum")
        collector.record_backtest_run("mean_reversion")

    def test_set_active_connections(self):
        """Test setting active connections gauge"""
        collector = MetricsCollector()
        collector.set_active_connections(5)
        collector.set_active_connections(10)

    def test_record_app_error(self):
        """Test recording application errors"""
        collector = MetricsCollector()
        collector.record_app_error("ValueError")
        collector.record_app_error("RuntimeError")

    def test_record_celery_task(self):
        """Test recording Celery task metrics"""
        collector = MetricsCollector()
        collector.record_celery_task("fetch_stock_prices", "success", 5.0)
        collector.record_celery_task("fetch_news", "failure", 10.0)
        collector.record_celery_task("health_check", "success")  # Without duration

    def test_record_celery_retry(self):
        """Test recording Celery task retries"""
        collector = MetricsCollector()
        collector.record_celery_retry("fetch_stock_prices")
        collector.record_celery_retry("fetch_news")

    def test_record_dead_letter(self):
        """Test recording dead letter queue entries"""
        collector = MetricsCollector()
        collector.record_dead_letter("fetch_stock_prices", "NetworkError")
        collector.record_dead_letter("fetch_news", "RateLimitError")

    def test_get_metrics_output(self):
        """Test getting metrics output"""
        collector = MetricsCollector()
        output = collector.get_metrics_output()
        assert isinstance(output, str)
        if PROMETHEUS_AVAILABLE:
            # Should contain some metric names
            assert len(output) > 0
        else:
            assert output == "Prometheus not available"


class TestGlobalMetricsInstance:
    """Tests for the global metrics instance"""

    def test_global_metrics_exists(self):
        """Test that global metrics instance exists"""
        assert metrics is not None
        assert isinstance(metrics, MetricsCollector)

    def test_global_metrics_record_http(self):
        """Test global metrics can record HTTP requests"""
        metrics.record_http_request("GET", "/test", 200, 0.01)

    def test_global_metrics_record_error(self):
        """Test global metrics can record errors"""
        metrics.record_app_error("TestError")


class TestTrackRequestMetrics:
    """Tests for track_request_metrics decorator"""

    @pytest.mark.asyncio
    async def test_track_request_metrics_success(self):
        """Test decorator tracks successful requests"""
        @track_request_metrics("/api/test")
        async def sample_endpoint():
            return {"status": "ok"}

        result = await sample_endpoint()
        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_track_request_metrics_exception(self):
        """Test decorator handles exceptions"""
        @track_request_metrics("/api/test")
        async def failing_endpoint():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await failing_endpoint()


class TestTrackPredictionMetrics:
    """Tests for track_prediction_metrics decorator"""

    @pytest.mark.asyncio
    async def test_track_prediction_success(self):
        """Test decorator tracks prediction metrics"""
        @track_prediction_metrics("test_model")
        async def make_prediction():
            return {"prediction": 0.75}

        result = await make_prediction()
        assert result == {"prediction": 0.75}


class TestTrackDbQuery:
    """Tests for track_db_query decorator"""

    @pytest.mark.asyncio
    async def test_track_db_query_async(self):
        """Test decorator tracks async database queries"""
        @track_db_query("SELECT")
        async def async_query():
            return [{"id": 1}]

        result = await async_query()
        assert result == [{"id": 1}]

    def test_track_db_query_sync(self):
        """Test decorator tracks sync database queries"""
        @track_db_query("INSERT")
        def sync_query():
            return {"inserted_id": 1}

        result = sync_query()
        assert result == {"inserted_id": 1}


class TestMetricsWithPrometheusDisabled:
    """Tests for metrics when Prometheus is not available"""

    def test_metrics_without_prometheus(self):
        """Test metrics work gracefully without Prometheus"""
        with patch.dict('app.metrics.__dict__', {'PROMETHEUS_AVAILABLE': False}):
            collector = MetricsCollector()
            # All methods should not raise
            collector.record_http_request("GET", "/test", 200, 0.1)
            collector.record_api_error("/test", "ERROR")
            collector.record_prediction("model", 0.1)
            collector.record_cache_hit("redis")
            collector.record_cache_miss("redis")
            collector.record_db_query("SELECT", 0.01)
            collector.record_stock_analyzed()
            collector.record_backtest_run("test")
            collector.set_active_connections(5)
            collector.record_app_error("Error")
            collector.record_celery_task("task", "success")
            collector.record_celery_retry("task")
            collector.record_dead_letter("task", "Error")
