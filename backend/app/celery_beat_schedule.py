"""
Celery Beat Scheduler Configuration
Defines periodic task schedules for intelligent data refresh

Schedule Strategy (Scale-Optimized):
- HOURLY: Current prices during market hours (9 AM - 3 PM IST, Mon-Fri)
- DAILY: Append OHLCV after market close (4:30 PM IST)
- DAILY: Refresh company info (6 AM IST)
- WEEKLY: Check for new quarterly results (Sunday 2 AM)
- MONTHLY: Check for new annual reports (1st of month, 3 AM)
"""

import os
from celery.schedules import crontab
from datetime import timedelta

# Load schedule intervals from environment variables
NEWS_FETCH_INTERVAL = int(os.getenv("NEWS_FETCH_INTERVAL", "1800"))  # 30 minutes
HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))  # 1 minute
ALERT_CHECK_INTERVAL = int(os.getenv("ALERT_CHECK_INTERVAL", "60"))  # 1 minute


# Celery Beat Schedule Configuration - Intelligent Refresh Strategy
CELERY_BEAT_SCHEDULE = {
    # =========================================================================
    # HOURLY: Price updates during market hours (scalable for 1000s of stocks)
    # Schedule: 9 AM, 10 AM, 11 AM, 12 PM, 1 PM, 2 PM, 3 PM IST (Mon-Fri)
    # =========================================================================
    "fetch_stock_prices": {
        "task": "app.tasks.fetch_stock_prices_task",
        "schedule": crontab(minute=0, hour="9-15", day_of_week="1-5"),
        "args": (),
        "kwargs": {},
        "options": {
            "queue": "stocks",
            "expires": 3600,  # Expire after 1 hour
            "retry": True,
            "retry_policy": {
                "max_retries": 3,
                "interval_start": 60,
                "interval_step": 60,
                "interval_max": 300,
            },
        },
    },

    # =========================================================================
    # DAILY: Append final OHLCV candle after market close
    # Schedule: 4:30 PM IST (Mon-Fri) - 1 hour after NSE close
    # =========================================================================
    "append_daily_ohlcv": {
        "task": "app.tasks.append_daily_ohlcv_task",
        "schedule": crontab(minute=30, hour=16, day_of_week="1-5"),
        "args": (),
        "kwargs": {},
        "options": {
            "queue": "stocks",
            "expires": 7200,  # Expire after 2 hours
            "retry": True,
            "retry_policy": {
                "max_retries": 3,
                "interval_start": 300,
                "interval_step": 300,
                "interval_max": 1800,
            },
        },
    },

    # =========================================================================
    # DAILY: Refresh company info (metrics, ratios, sector)
    # Schedule: 6 AM IST daily - before market opens
    # =========================================================================
    "refresh_company_info": {
        "task": "app.tasks.refresh_company_info_task",
        "schedule": crontab(minute=0, hour=6),
        "args": (),
        "kwargs": {},
        "options": {
            "queue": "stocks",
            "expires": 10800,  # Expire after 3 hours
            "retry": True,
            "retry_policy": {
                "max_retries": 3,
                "interval_start": 300,
                "interval_step": 300,
                "interval_max": 1800,
            },
        },
    },

    # =========================================================================
    # WEEKLY: Check for new quarterly results
    # Schedule: Sunday 2 AM IST - minimal impact on system
    # =========================================================================
    "weekly_quarterly_sync": {
        "task": "app.tasks.weekly_quarterly_sync_task",
        "schedule": crontab(minute=0, hour=2, day_of_week=0),
        "args": (),
        "kwargs": {},
        "options": {
            "queue": "stocks",
            "expires": 86400,  # Expire after 1 day
            "retry": True,
            "retry_policy": {
                "max_retries": 3,
                "interval_start": 600,
                "interval_step": 600,
                "interval_max": 3600,
            },
        },
    },

    # =========================================================================
    # MONTHLY: Check for new annual reports
    # Schedule: 1st of month, 3 AM IST
    # =========================================================================
    "monthly_annual_sync": {
        "task": "app.tasks.monthly_annual_sync_task",
        "schedule": crontab(minute=0, hour=3, day_of_month=1),
        "args": (),
        "kwargs": {},
        "options": {
            "queue": "stocks",
            "expires": 86400,  # Expire after 1 day
            "retry": True,
            "retry_policy": {
                "max_retries": 3,
                "interval_start": 600,
                "interval_step": 600,
                "interval_max": 3600,
            },
        },
    },

    # =========================================================================
    # NEWS: Fetch news articles every 30 minutes
    # =========================================================================
    "fetch_news": {
        "task": "app.tasks.fetch_news_task",
        "schedule": timedelta(seconds=NEWS_FETCH_INTERVAL),
        "args": (),
        "kwargs": {},
        "options": {
            "queue": "news",
            "expires": NEWS_FETCH_INTERVAL + 60,
            "retry": True,
            "retry_policy": {
                "max_retries": 2,
                "interval_start": 120,
                "interval_step": 120,
                "interval_max": 600,
            },
        },
    },

    # =========================================================================
    # HEALTH: Health check every 1 minute
    # =========================================================================
    "health_check": {
        "task": "app.tasks.health_check",
        "schedule": timedelta(seconds=HEALTH_CHECK_INTERVAL),
        "args": (),
        "kwargs": {},
        "options": {
            "queue": "default",
            "expires": 70,
        },
    },

    # =========================================================================
    # ALERTS: Check alerts every 1 minute
    # =========================================================================
    "check_alerts": {
        "task": "app.tasks.check_alerts_task",
        "schedule": timedelta(seconds=ALERT_CHECK_INTERVAL),
        "args": (),
        "kwargs": {},
        "options": {
            "queue": "default",
            "expires": 120,
        },
    },

    # =========================================================================
    # WEEKLY: Regenerate correlations (Sunday 2:30 AM, after quarterly sync)
    # =========================================================================
    "regenerate_correlations": {
        "task": "app.tasks.regenerate_correlations_task",
        "schedule": crontab(minute=30, hour=2, day_of_week=0),
        "args": (),
        "kwargs": {},
        "options": {
            "queue": "analysis",
            "expires": 86400,
            "retry": True,
            "retry_policy": {
                "max_retries": 3,
                "interval_start": 300,
                "interval_step": 300,
                "interval_max": 3600,
            },
        },
    },
}


# Configuration documentation
"""
INTELLIGENT DATA REFRESH SCHEDULE
=================================

This configuration implements a scale-optimized refresh strategy that balances
data freshness with API rate limits and system resources.

Schedule Overview:
------------------
┌────────────────────┬───────────────────────────────────────────────────────┐
│ Task               │ Schedule                                              │
├────────────────────┼───────────────────────────────────────────────────────┤
│ Price Updates      │ Hourly (9 AM - 3 PM IST, Mon-Fri)                    │
│ Daily OHLCV        │ 4:30 PM IST (Mon-Fri, after market close)            │
│ Company Info       │ 6:00 AM IST (Daily, before market)                   │
│ Quarterly Sync     │ Sunday 2:00 AM IST (Weekly)                          │
│ Annual Sync        │ 1st of month, 3:00 AM IST (Monthly)                  │
│ News               │ Every 30 minutes                                      │
│ Health Check       │ Every 1 minute                                        │
│ Alerts             │ Every 1 minute                                        │
│ Correlations       │ Sunday 2:30 AM IST (Weekly, after quarterly sync)    │
└────────────────────┴───────────────────────────────────────────────────────┘

Task Descriptions:
------------------
1. fetch_stock_prices_task
   - Schedule: Hourly during market hours (9 AM - 3 PM IST, Mon-Fri)
   - Purpose: Update current prices for all tracked stocks
   - Scalable: 1-hour window allows processing 1000s of stocks

2. append_daily_ohlcv_task
   - Schedule: 4:30 PM IST (Mon-Fri)
   - Purpose: Append today's final OHLCV candle to price history
   - Keeps charts fresh without continuous polling

3. refresh_company_info_task
   - Schedule: 6 AM IST daily
   - Purpose: Update metrics (P/E, ROE, ROCE, Market Cap, etc.)
   - Catches changes from Screener.in/Yahoo Finance

4. weekly_quarterly_sync_task
   - Schedule: Sunday 2 AM IST
   - Purpose: Check for and fetch new quarterly results
   - Incremental: Only fetches NEW quarters, not all 13+

5. monthly_annual_sync_task
   - Schedule: 1st of month, 3 AM IST
   - Purpose: Check for and fetch new annual reports
   - Runs once per month to catch annual filings

Why This Schedule:
------------------
- SCALE: 1-hour price updates vs 5-minute allows 12x more stocks
- FRESHNESS: Daily OHLCV keeps charts current without real-time polling
- EFFICIENCY: Quarterly/annual data rarely changes, weekly/monthly checks suffice
- COST: Reduces API calls by 90%+ compared to aggressive polling

Environment Variables:
----------------------
NEWS_FETCH_INTERVAL     - News fetch interval in seconds (default: 1800)
HEALTH_CHECK_INTERVAL   - Health check interval in seconds (default: 60)
ALERT_CHECK_INTERVAL    - Alert check interval in seconds (default: 60)

Note: Price/financial schedules use crontab (market-hours aware) and are
not configurable via environment variables for consistency.

Testing Tasks:
--------------
    celery -A app.tasks call app.tasks.fetch_stock_prices_task
    celery -A app.tasks call app.tasks.append_daily_ohlcv_task
    celery -A app.tasks call app.tasks.refresh_company_info_task
    celery -A app.tasks call app.tasks.weekly_quarterly_sync_task
    celery -A app.tasks call app.tasks.monthly_annual_sync_task
"""
