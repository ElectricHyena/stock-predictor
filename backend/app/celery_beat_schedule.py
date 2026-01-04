"""
Celery Beat Scheduler Configuration
Defines periodic task schedules for background data fetching
"""

import os
from celery.schedules import schedule
from datetime import timedelta

# Load schedule intervals from environment variables (in seconds)
STOCK_FETCH_INTERVAL = int(os.getenv("STOCK_FETCH_INTERVAL", "300"))  # 5 minutes
NEWS_FETCH_INTERVAL = int(os.getenv("NEWS_FETCH_INTERVAL", "1800"))  # 30 minutes
HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))  # 1 minute
CORRELATION_REGEN_INTERVAL = int(os.getenv("CORRELATION_REGEN_INTERVAL", "604800"))  # 7 days
ALERT_CHECK_INTERVAL = int(os.getenv("ALERT_CHECK_INTERVAL", "60"))  # 1 minute


# Celery Beat Schedule Configuration
CELERY_BEAT_SCHEDULE = {
    # Stock price update task - every 5 minutes
    "fetch_stock_prices": {
        "task": "app.tasks.fetch_stock_prices_task",
        "schedule": timedelta(seconds=STOCK_FETCH_INTERVAL),
        "args": (),
        "kwargs": {},
        "options": {
            "queue": "stocks",
            "expires": STOCK_FETCH_INTERVAL + 60,  # Task expires after interval + 1min
            "retry": True,
            "retry_policy": {
                "max_retries": 3,
                "interval_start": 60,
                "interval_step": 60,
                "interval_max": 300,
            },
        },
        "description": "Fetch stock prices for all tracked stocks (SLO: 5 minutes)",
    },
    # News update task - every 30 minutes
    "fetch_news": {
        "task": "app.tasks.fetch_news_task",
        "schedule": timedelta(seconds=NEWS_FETCH_INTERVAL),
        "args": (),
        "kwargs": {},
        "options": {
            "queue": "news",
            "expires": NEWS_FETCH_INTERVAL + 60,  # Task expires after interval + 1min
            "retry": True,
            "retry_policy": {
                "max_retries": 2,  # Fewer retries for rate-limited API
                "interval_start": 120,
                "interval_step": 120,
                "interval_max": 600,
            },
        },
        "description": "Fetch news articles for all tracked stocks (SLO: 30 minutes)",
    },
    # Health check task - every 1 minute
    "health_check": {
        "task": "app.tasks.health_check",
        "schedule": timedelta(seconds=HEALTH_CHECK_INTERVAL),
        "args": (),
        "kwargs": {},
        "options": {
            "queue": "default",
            "expires": 70,
        },
        "description": "Health check to verify Celery worker is operational",
    },
    # Correlation regeneration task - weekly
    "regenerate_correlations": {
        "task": "app.tasks.regenerate_correlations_task",
        "schedule": timedelta(seconds=CORRELATION_REGEN_INTERVAL),
        "args": (),
        "kwargs": {},
        "options": {
            "queue": "analysis",
            "expires": 86400,  # Expire after 1 day
            "retry": True,
            "retry_policy": {
                "max_retries": 3,
                "interval_start": 300,
                "interval_step": 300,
                "interval_max": 3600,
            },
        },
        "description": "Regenerate event-price correlations for all stocks (weekly)",
    },
    # Alert check task - every 1 minute
    "check_alerts": {
        "task": "app.tasks.check_alerts_task",
        "schedule": timedelta(seconds=ALERT_CHECK_INTERVAL),
        "args": (),
        "kwargs": {},
        "options": {
            "queue": "default",
            "expires": 120,
        },
        "description": "Check and trigger alerts based on current conditions",
    },
}


# Configuration documentation
"""
CELERY BEAT SCHEDULE CONFIGURATION

Overview:
---------
This configuration defines periodic tasks that run on a schedule using Celery Beat.
All intervals are configurable via environment variables for flexibility.

Default Schedules:
------------------
1. fetch_stock_prices_task
   - Interval: 5 minutes (STOCK_FETCH_INTERVAL env var)
   - Queue: stocks
   - Purpose: Fetch OHLCV data for all tracked stocks from Yahoo Finance
   - SLO Target: Complete within 5 minutes
   - Retry: 3 attempts with 60-300s exponential backoff

2. fetch_news_task
   - Interval: 30 minutes (NEWS_FETCH_INTERVAL env var)
   - Queue: news
   - Purpose: Fetch latest news articles for all tracked stocks from NewsAPI
   - SLO Target: Complete within 30 minutes
   - Retry: 2 attempts (fewer due to API rate limits)

3. health_check
   - Interval: 1 minute (HEALTH_CHECK_INTERVAL env var)
   - Queue: default
   - Purpose: Verify Celery worker and database connectivity
   - Auto-cleanup: Tasks expire after interval + 10 seconds

Environment Variables:
----------------------
STOCK_FETCH_INTERVAL    - Stock fetch interval in seconds (default: 300 = 5 min)
NEWS_FETCH_INTERVAL     - News fetch interval in seconds (default: 1800 = 30 min)
HEALTH_CHECK_INTERVAL   - Health check interval in seconds (default: 60 = 1 min)

Example .env:
    STOCK_FETCH_INTERVAL=300      # Update stocks every 5 minutes
    NEWS_FETCH_INTERVAL=1800       # Update news every 30 minutes
    HEALTH_CHECK_INTERVAL=300      # Health check every 5 minutes

Task Queue Routing:
-------------------
- Stock tasks route to 'stocks' queue for dedicated worker
- News tasks route to 'news' queue (can be separate worker)
- Health checks use 'default' queue

Error Handling:
---------------
- Network/API errors: Exponential backoff (60s, 120s, 240s)
- Rate limit errors: Longer backoff (5 min for stocks, 1 hour for news)
- Task timeout: Hard limit 10 min, soft limit 9 min
- Failed tasks: Logged with full traceback
- Database errors: Task fails and is retried on next interval

Monitoring:
-----------
- Task execution is logged with task ID and metrics
- Each task returns status dict with processed count and errors
- Health check verifies database and Celery connectivity
- Task results cached in Redis for 1 hour

Scaling:
--------
For production:
1. Multiple Celery workers can consume from 'stocks' queue
2. Separate worker can handle 'news' queue (rate limit protection)
3. Beat scheduler should run on single node only (or use distributed lock)
4. Adjust intervals based on data freshness requirements and API limits

Development:
-------------
To test tasks manually:
    celery -A app.tasks call app.tasks.fetch_stock_prices_task
    celery -A app.tasks call app.tasks.fetch_news_task
"""
