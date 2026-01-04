"""
Prometheus Metrics Collection and Monitoring
"""
import time
from datetime import datetime
from typing import Dict, List, Optional
from functools import wraps

try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Summary,
        CollectorRegistry, generate_latest
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class MetricsCollector:
    """Collect and expose Prometheus metrics"""

    def __init__(self):
        if PROMETHEUS_AVAILABLE:
            self.registry = CollectorRegistry()

            # HTTP Metrics
            self.http_requests = Counter(
                "http_requests_total",
                "Total HTTP requests",
                ["method", "endpoint", "status"],
                registry=self.registry
            )

            self.http_request_duration = Histogram(
                "http_request_duration_seconds",
                "HTTP request duration in seconds",
                ["method", "endpoint"],
                buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0),
                registry=self.registry
            )

            # API Metrics
            self.api_errors = Counter(
                "api_errors_total",
                "Total API errors",
                ["endpoint", "error_code"],
                registry=self.registry
            )

            # Model Metrics
            self.predictions_made = Counter(
                "predictions_made_total",
                "Total predictions made",
                ["model_type"],
                registry=self.registry
            )

            self.prediction_latency = Histogram(
                "prediction_latency_seconds",
                "Prediction inference time in seconds",
                ["model_type"],
                buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
                registry=self.registry
            )

            # Cache Metrics
            self.cache_hits = Counter(
                "cache_hits_total",
                "Total cache hits",
                ["cache_type"],
                registry=self.registry
            )

            self.cache_misses = Counter(
                "cache_misses_total",
                "Total cache misses",
                ["cache_type"],
                registry=self.registry
            )

            # Database Metrics
            self.db_queries = Counter(
                "db_queries_total",
                "Total database queries",
                ["operation"],
                registry=self.registry
            )

            self.db_query_duration = Histogram(
                "db_query_duration_seconds",
                "Database query duration in seconds",
                ["operation"],
                buckets=(0.001, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0),
                registry=self.registry
            )

            # Business Metrics
            self.stocks_analyzed = Counter(
                "stocks_analyzed_total",
                "Total stocks analyzed",
                registry=self.registry
            )

            self.backtest_runs = Counter(
                "backtest_runs_total",
                "Total backtest runs",
                ["strategy"],
                registry=self.registry
            )

            # System Health Metrics
            self.active_connections = Gauge(
                "active_connections",
                "Active database connections",
                registry=self.registry
            )

            self.app_errors = Counter(
                "app_errors_total",
                "Total application errors",
                ["error_type"],
                registry=self.registry
            )

            # Celery Task Metrics
            self.celery_task_total = Counter(
                "celery_task_total",
                "Total Celery tasks executed",
                ["task_name", "status"],
                registry=self.registry
            )

            self.celery_task_duration = Histogram(
                "celery_task_duration_seconds",
                "Celery task execution duration in seconds",
                ["task_name"],
                buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
                registry=self.registry
            )

            self.celery_task_retries = Counter(
                "celery_task_retries_total",
                "Total Celery task retries",
                ["task_name"],
                registry=self.registry
            )

            self.celery_dead_letter_queue = Counter(
                "celery_dead_letter_queue_total",
                "Tasks moved to dead letter queue",
                ["task_name", "exception_type"],
                registry=self.registry
            )
        else:
            self.metrics_data = {}

    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        if PROMETHEUS_AVAILABLE:
            self.http_requests.labels(method=method, endpoint=endpoint, status=status_code).inc()
            self.http_request_duration.labels(method=method, endpoint=endpoint).observe(duration)

    def record_api_error(self, endpoint: str, error_code: str):
        """Record API error"""
        if PROMETHEUS_AVAILABLE:
            self.api_errors.labels(endpoint=endpoint, error_code=error_code).inc()

    def record_prediction(self, model_type: str, latency: float):
        """Record prediction metrics"""
        if PROMETHEUS_AVAILABLE:
            self.predictions_made.labels(model_type=model_type).inc()
            self.prediction_latency.labels(model_type=model_type).observe(latency)

    def record_cache_hit(self, cache_type: str):
        """Record cache hit"""
        if PROMETHEUS_AVAILABLE:
            self.cache_hits.labels(cache_type=cache_type).inc()

    def record_cache_miss(self, cache_type: str):
        """Record cache miss"""
        if PROMETHEUS_AVAILABLE:
            self.cache_misses.labels(cache_type=cache_type).inc()

    def record_db_query(self, operation: str, duration: float):
        """Record database query metrics"""
        if PROMETHEUS_AVAILABLE:
            self.db_queries.labels(operation=operation).inc()
            self.db_query_duration.labels(operation=operation).observe(duration)

    def record_stock_analyzed(self):
        """Record stock analyzed"""
        if PROMETHEUS_AVAILABLE:
            self.stocks_analyzed.inc()

    def record_backtest_run(self, strategy: str):
        """Record backtest run"""
        if PROMETHEUS_AVAILABLE:
            self.backtest_runs.labels(strategy=strategy).inc()

    def set_active_connections(self, count: int):
        """Set active database connections"""
        if PROMETHEUS_AVAILABLE:
            self.active_connections.set(count)

    def record_app_error(self, error_type: str):
        """Record application error"""
        if PROMETHEUS_AVAILABLE:
            self.app_errors.labels(error_type=error_type).inc()

    def record_celery_task(self, task_name: str, status: str, duration: float = None):
        """Record Celery task execution"""
        if PROMETHEUS_AVAILABLE:
            self.celery_task_total.labels(task_name=task_name, status=status).inc()
            if duration is not None:
                self.celery_task_duration.labels(task_name=task_name).observe(duration)

    def record_celery_retry(self, task_name: str):
        """Record Celery task retry"""
        if PROMETHEUS_AVAILABLE:
            self.celery_task_retries.labels(task_name=task_name).inc()

    def record_dead_letter(self, task_name: str, exception_type: str):
        """Record task moved to dead letter queue"""
        if PROMETHEUS_AVAILABLE:
            self.celery_dead_letter_queue.labels(
                task_name=task_name,
                exception_type=exception_type
            ).inc()

    def get_metrics_output(self) -> str:
        """Get Prometheus metrics output"""
        if PROMETHEUS_AVAILABLE:
            return generate_latest(self.registry).decode("utf-8")
        return "Prometheus not available"


# Global metrics instance
metrics = MetricsCollector()


def track_request_metrics(endpoint: str):
    """Decorator to track HTTP request metrics"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                # Metrics would be recorded by middleware
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_app_error(type(e).__name__)
                raise

        return async_wrapper
    return decorator


def track_prediction_metrics(model_type: str):
    """Decorator to track prediction metrics"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            metrics.record_prediction(model_type, duration)
            return result

        return async_wrapper
    return decorator


def track_db_query(operation: str):
    """Decorator to track database query metrics"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            metrics.record_db_query(operation, duration)
            return result

        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            metrics.record_db_query(operation, duration)
            return result

        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
