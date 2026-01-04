"""
Celery Configuration
Configures Celery app for async background task processing
"""

import os
from celery import Celery
from kombu import Queue, Exchange
from datetime import timedelta

from app.celery_beat_schedule import CELERY_BEAT_SCHEDULE

# Create Celery app
celery_app = Celery(__name__)

# Load configuration from environment
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

# Celery configuration
celery_app.conf.update(
    # Broker and backend settings
    broker_url=BROKER_URL,
    result_backend=RESULT_BACKEND,

    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution settings
    task_track_started=True,
    task_time_limit=600,  # 10 minutes hard limit
    task_soft_time_limit=540,  # 9 minutes soft limit
    task_acks_late=True,  # Acknowledge after task completes
    worker_prefetch_multiplier=4,  # Prefetch tasks

    # Retry settings
    task_autoretry_for=(Exception,),
    task_max_retries=3,
    task_default_retry_delay=60,  # 1 minute between retries

    # Result backend settings
    result_expires=3600,  # Keep results for 1 hour
    result_extended=True,

    # Beat scheduler settings
    beat_scheduler="celery.beat:PersistentScheduler",
    beat_schedule=CELERY_BEAT_SCHEDULE,

    # Queue configuration
    task_queues=(
        Queue(
            "default",
            Exchange("default", type="direct"),
            routing_key="default",
        ),
        Queue(
            "stocks",
            Exchange("stocks", type="direct"),
            routing_key="stocks",
        ),
        Queue(
            "news",
            Exchange("news", type="direct"),
            routing_key="news",
        ),
        Queue(
            "analysis",
            Exchange("analysis", type="direct"),
            routing_key="analysis",
        ),
        Queue(
            "backtest",
            Exchange("backtest", type="direct"),
            routing_key="backtest",
        ),
        Queue(
            "dead_letter",
            Exchange("dead_letter", type="direct"),
            routing_key="dead_letter",
        ),
    ),
    task_default_queue="default",

    # Task routing
    task_routes={
        "app.tasks.fetch_stock_prices_task": {"queue": "stocks"},
        "app.tasks.fetch_news_task": {"queue": "news"},
        "app.tasks.regenerate_correlations_task": {"queue": "analysis"},
        "app.tasks.run_backtest_task": {"queue": "backtest"},
        "app.tasks.check_alerts_task": {"queue": "default"},
    },

    # Worker settings
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
)

# Task default options
celery_app.conf.task_default_kwargs = {
    "max_retries": 3,
    "default_retry_delay": 60,
}

# Configure periodic task execution
celery_app.conf.task_compression = "gzip"

# Logging configuration
celery_app.conf.worker_log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
celery_app.conf.worker_task_log_format = (
    "[%(asctime)s] [%(levelname)s] [%(name)s:%(taskname)s:%(task_id)s] %(message)s"
)
