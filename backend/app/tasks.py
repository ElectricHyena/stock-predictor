"""
Celery Background Tasks
Handles async data fetching for stock prices and news articles
"""

import logging
import os
import time
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from celery.signals import task_prerun, task_postrun, task_failure, task_retry

from app.celery_config import celery_app
from app.database import SessionLocal
from app.models import Stock
from app.services.data_fetchers import YahooFinanceFetcher
from app.services.news_fetchers import NewsAPIFetcher
from app.services.smart_data_manager import SmartDataManager, SyncType
from app.exceptions import (
    APIError,
    NetworkError,
    DatabaseError,
    RateLimitError,
    InvalidTickerError,
)
from app.metrics import metrics

# Configure logging for tasks
logger = logging.getLogger(__name__)

# Store task start times for duration calculation
_task_start_times: Dict[str, float] = {}


# ============================================================================
# Celery Signal Handlers for Metrics and Dead Letter Queue
# ============================================================================

@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    """Record task start time for duration calculation"""
    _task_start_times[task_id] = time.time()
    logger.debug(f"Task {task.name} [{task_id}] starting")


@task_postrun.connect
def task_postrun_handler(task_id, task, retval, state, *args, **kwargs):
    """Record task completion metrics"""
    start_time = _task_start_times.pop(task_id, None)
    duration = time.time() - start_time if start_time else None

    status = "success" if state == "SUCCESS" else "failure"
    metrics.record_celery_task(task.name, status, duration)

    logger.debug(
        f"Task {task.name} [{task_id}] completed with state={state}, "
        f"duration={duration:.2f}s" if duration else f"Task {task.name} [{task_id}] completed"
    )


@task_retry.connect
def task_retry_handler(request, reason, einfo, *args, **kwargs):
    """Record task retry metrics"""
    task_name = request.task if hasattr(request, 'task') else 'unknown'
    metrics.record_celery_retry(task_name)
    logger.warning(f"Task {task_name} [{request.id}] retrying: {reason}")


@task_failure.connect
def task_failure_handler(task_id, exception, args, kwargs, traceback, einfo, sender, *extra_args, **extra_kwargs):
    """
    Handle task failures - move to dead letter queue after max retries exhausted.

    This handler:
    1. Records failure metrics
    2. Logs the failure with full context
    3. Publishes failed task info to dead_letter queue for manual inspection
    """
    task_name = sender.name if sender else 'unknown'
    exception_type = type(exception).__name__

    # Record metrics
    metrics.record_celery_task(task_name, "failure")
    metrics.record_dead_letter(task_name, exception_type)

    # Build dead letter message
    dead_letter_msg = {
        "task_id": task_id,
        "task_name": task_name,
        "args": str(args),
        "kwargs": str(kwargs),
        "exception_type": exception_type,
        "exception_message": str(exception),
        "traceback": str(einfo) if einfo else None,
        "failed_at": datetime.utcnow().isoformat(),
    }

    logger.error(
        f"Task {task_name} [{task_id}] failed permanently: {exception_type}: {exception}. "
        f"Moving to dead letter queue."
    )

    # Publish to dead letter queue
    try:
        celery_app.send_task(
            "app.tasks.dead_letter_handler",
            args=[dead_letter_msg],
            queue="dead_letter",
        )
    except Exception as e:
        logger.error(f"Failed to publish to dead letter queue: {e}")


@celery_app.task(
    bind=True,
    name="app.tasks.dead_letter_handler",
    queue="dead_letter",
    max_retries=0,  # Don't retry DLQ handler
)
def dead_letter_handler(self, failed_task_info: Dict) -> Dict:
    """
    Handle tasks that have been moved to the dead letter queue.

    This task receives failed task information and can be used for:
    - Alerting (email, Slack, PagerDuty)
    - Storing in a failures table for later analysis
    - Attempting manual recovery

    Args:
        failed_task_info: Dict containing failed task details

    Returns:
        Dict with handling result
    """
    task_id = failed_task_info.get("task_id", "unknown")
    task_name = failed_task_info.get("task_name", "unknown")

    logger.info(f"Dead letter handler received failed task: {task_name} [{task_id}]")

    # Log the full failure details
    logger.error(
        f"DEAD LETTER: task={task_name}, id={task_id}, "
        f"exception={failed_task_info.get('exception_type')}: "
        f"{failed_task_info.get('exception_message')}"
    )

    # TODO: Add alerting integration (Slack, email, etc.)
    # TODO: Store in database for failure analysis

    return {
        "status": "logged",
        "task_id": task_id,
        "task_name": task_name,
        "handled_at": datetime.utcnow().isoformat(),
    }


# Task configuration from environment
STOCK_FETCH_INTERVAL = int(os.getenv("STOCK_FETCH_INTERVAL", "300"))  # 5 minutes
NEWS_FETCH_INTERVAL = int(os.getenv("NEWS_FETCH_INTERVAL", "1800"))  # 30 minutes
NEWS_DAYS_BACK = int(os.getenv("NEWS_DAYS_BACK", "7"))  # 7 days


def get_db_session() -> Session:
    """
    Get a new database session for the task.

    Returns:
        SQLAlchemy Session instance
    """
    return SessionLocal()


def get_tracked_stocks(db: Session) -> List[Dict[str, any]]:
    """
    Get all active stocks to track.

    Args:
        db: Database session

    Returns:
        List of stock dictionaries with id, ticker, and company_name

    Raises:
        DatabaseError: If database query fails
    """
    try:
        stocks = db.query(Stock).all()

        if not stocks:
            logger.warning("No stocks found in database")
            return []

        stock_list = [
            {
                "id": stock.id,
                "ticker": stock.ticker,
                "name": stock.company_name,
            }
            for stock in stocks
        ]

        logger.info(f"Found {len(stock_list)} stocks to track")
        return stock_list

    except Exception as e:
        logger.error(f"Failed to retrieve tracked stocks: {str(e)}")
        raise DatabaseError(f"Failed to retrieve stocks: {str(e)}") from e


@celery_app.task(
    bind=True,
    name="app.tasks.fetch_stock_prices_task",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def fetch_stock_prices_task(self) -> Dict[str, any]:
    """
    Celery task to fetch and update stock prices for all tracked stocks.

    Fetches OHLCV data from Yahoo Finance and stores in database.
    Implements retry logic with exponential backoff for transient failures.

    Returns:
        Dict with status, fetched, stored, and error counts

    Task Configuration:
        - Queue: stocks
        - Max Retries: 3
        - Soft Time Limit: 540s (9 min)
        - Hard Time Limit: 600s (10 min)
        - Retry Delay: 60s (exponential backoff)

    SLO Target: 5 minutes
    """
    task_id = self.request.id
    db = None

    try:
        logger.info(f"[{task_id}] Starting stock price fetch task")

        # Get database session
        db = get_db_session()

        # Get list of tracked stocks
        stocks = get_tracked_stocks(db)

        if not stocks:
            logger.warning(f"[{task_id}] No stocks to fetch")
            return {
                "status": "success",
                "fetched": 0,
                "stored": 0,
                "errors": 0,
                "message": "No stocks found",
            }

        # Initialize fetcher
        fetcher = YahooFinanceFetcher(db)

        # Fetch tickers
        tickers = [stock["ticker"] for stock in stocks]
        logger.info(f"[{task_id}] Fetching prices for {len(tickers)} stocks: {tickers}")

        # Fetch and save data
        results = fetcher.fetch_and_save_multiple(tickers)

        # Calculate metrics
        total_fetched = sum(1 for _ in results if results[_] != (0, 0))
        total_stored = sum(inserted for ticker, (inserted, _) in results.items())
        total_errors = sum(1 for _ in results if results[_] == (0, 0))

        logger.info(
            f"[{task_id}] Stock prices task completed: "
            f"fetched={total_fetched}, stored={total_stored}, errors={total_errors}"
        )

        return {
            "status": "success",
            "fetched": total_fetched,
            "stored": total_stored,
            "errors": total_errors,
            "stocks_processed": results,
        }

    except (NetworkError, APIError) as e:
        # Transient errors: retry with exponential backoff
        logger.warning(
            f"[{task_id}] Transient error in stock fetch: {str(e)}. "
            f"Retrying... (attempt {self.request.retries + 1}/{self.max_retries})"
        )

        # Exponential backoff: 60s, 120s, 240s
        retry_delay = 60 * (2 ** self.request.retries)

        raise self.retry(exc=e, countdown=retry_delay)

    except RateLimitError as e:
        # Rate limit: back off for longer
        logger.error(f"[{task_id}] Rate limited on stock fetch: {str(e)}")
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes

    except Exception as e:
        # Unexpected errors
        logger.error(
            f"[{task_id}] Unexpected error in stock fetch: {str(e)}",
            exc_info=True,
        )

        return {
            "status": "failed",
            "fetched": 0,
            "stored": 0,
            "errors": 1,
            "message": f"Task failed: {str(e)}",
        }

    finally:
        # Clean up database connection
        if db:
            try:
                db.close()
            except Exception as e:
                logger.warning(f"[{task_id}] Error closing database session: {str(e)}")


@celery_app.task(
    bind=True,
    name="app.tasks.fetch_news_task",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def fetch_news_task(self) -> Dict[str, any]:
    """
    Celery task to fetch and update news articles for all tracked stocks.

    Fetches news from NewsAPI and stores in database with deduplication.
    Implements retry logic with exponential backoff for transient failures.

    Returns:
        Dict with status, fetched, stored, and duplicate counts

    Task Configuration:
        - Queue: news
        - Max Retries: 3
        - Soft Time Limit: 540s (9 min)
        - Hard Time Limit: 600s (10 min)
        - Retry Delay: 60s (exponential backoff)

    SLO Target: 30 minutes
    """
    task_id = self.request.id
    db = None

    try:
        logger.info(f"[{task_id}] Starting news fetch task")

        # Get database session
        db = get_db_session()

        # Get list of tracked stocks
        stocks = get_tracked_stocks(db)

        if not stocks:
            logger.warning(f"[{task_id}] No stocks to fetch news for")
            return {
                "status": "success",
                "fetched": 0,
                "stored": 0,
                "duplicates": 0,
                "message": "No stocks found",
            }

        # Initialize fetcher
        fetcher = NewsAPIFetcher(db)

        logger.info(
            f"[{task_id}] Fetching news for {len(stocks)} stocks. "
            f"Days back: {NEWS_DAYS_BACK}"
        )

        # Fetch and save news for all stocks
        results = fetcher.fetch_and_save_multiple(
            stocks,
            days_back=NEWS_DAYS_BACK,
        )

        # Calculate metrics
        total_fetched = sum(1 for _ in results if results[_] != (0, 0))
        total_stored = sum(inserted for ticker, (inserted, _) in results.items())
        total_duplicates = sum(skipped for ticker, (_, skipped) in results.items())

        logger.info(
            f"[{task_id}] News fetch task completed: "
            f"fetched={total_fetched}, stored={total_stored}, duplicates={total_duplicates}"
        )

        return {
            "status": "success",
            "fetched": total_fetched,
            "stored": total_stored,
            "duplicates": total_duplicates,
            "stocks_processed": results,
        }

    except RateLimitError as e:
        # Rate limit: important to handle gracefully since NewsAPI has daily limits
        logger.error(f"[{task_id}] NewsAPI rate limit hit: {str(e)}")

        # Back off for a longer period to avoid burning quota
        raise self.retry(exc=e, countdown=3600)  # Retry after 1 hour

    except (NetworkError, APIError) as e:
        # Transient errors: retry with exponential backoff
        logger.warning(
            f"[{task_id}] Transient error in news fetch: {str(e)}. "
            f"Retrying... (attempt {self.request.retries + 1}/{self.max_retries})"
        )

        # Exponential backoff: 60s, 120s, 240s
        retry_delay = 60 * (2 ** self.request.retries)

        raise self.retry(exc=e, countdown=retry_delay)

    except Exception as e:
        # Unexpected errors
        logger.error(
            f"[{task_id}] Unexpected error in news fetch: {str(e)}",
            exc_info=True,
        )

        return {
            "status": "failed",
            "fetched": 0,
            "stored": 0,
            "duplicates": 0,
            "message": f"Task failed: {str(e)}",
        }

    finally:
        # Clean up database connection
        if db:
            try:
                db.close()
            except Exception as e:
                logger.warning(f"[{task_id}] Error closing database session: {str(e)}")


@celery_app.task(bind=True, name="app.tasks.health_check")
def health_check(self) -> Dict[str, any]:
    """
    Simple health check task to verify Celery worker is operational.

    Returns:
        Dict with status and timestamp
    """
    try:
        db = get_db_session()

        # Try to query database
        stock_count = db.query(Stock).count()
        db.close()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "stocks_in_db": stock_count,
        }

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }


@celery_app.task(
    bind=True,
    name="app.tasks.run_backtest_task",
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def run_backtest_task(
    self,
    ticker: str,
    start_date: str,
    end_date: str,
    initial_capital: float,
    strategy_name: str,
    entry_signal: str,
    exit_signal: str,
    position_size: float = 1.0,
    stop_loss_pct: Optional[float] = None,
    take_profit_pct: Optional[float] = None,
    max_holding_days: Optional[int] = None,
    slippage_pct: float = 0.1,
) -> Dict[str, any]:
    """
    Async Celery task to run backtest in background.

    This enables long-running backtests to execute without blocking the API.

    Args:
        ticker: Stock ticker symbol
        start_date: Backtest start date (ISO format)
        end_date: Backtest end date (ISO format)
        initial_capital: Starting capital
        strategy_name: Name of the strategy
        entry_signal: Entry signal type
        exit_signal: Exit signal type
        position_size: Position size multiplier
        stop_loss_pct: Stop loss percentage
        take_profit_pct: Take profit percentage
        max_holding_days: Maximum days to hold position
        slippage_pct: Slippage percentage

    Returns:
        Dict with backtest results or error
    """
    task_id = self.request.id
    db = None

    try:
        logger.info(f"[{task_id}] Starting async backtest for {ticker}")

        from datetime import date as date_type
        from app.api.backtest import BacktestEngine
        from app import schemas

        # Parse dates
        start = date_type.fromisoformat(start_date)
        end = date_type.fromisoformat(end_date)

        # Build request
        strategy = schemas.BacktestStrategy(
            name=strategy_name,
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            position_size=position_size,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            max_holding_days=max_holding_days,
        )

        request = schemas.BacktestRequest(
            ticker=ticker,
            start_date=start,
            end_date=end,
            initial_capital=initial_capital,
            strategy=strategy,
            slippage_pct=slippage_pct,
        )

        # Get database session
        db = get_db_session()

        # Run backtest
        engine = BacktestEngine(db)
        result = engine.run_backtest(request)

        logger.info(
            f"[{task_id}] Backtest completed for {ticker}: "
            f"return={result.total_return_pct:.2f}%, trades={result.num_trades}"
        )

        return {
            "status": "completed",
            "task_id": task_id,
            "result": result.model_dump(mode='json'),
        }

    except ValueError as e:
        logger.error(f"[{task_id}] Backtest validation error: {str(e)}")
        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(e),
        }

    except Exception as e:
        logger.error(f"[{task_id}] Backtest error: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "task_id": task_id,
            "error": f"Backtest failed: {str(e)}",
        }

    finally:
        if db:
            try:
                db.close()
            except Exception as e:
                logger.warning(f"[{task_id}] Error closing database: {str(e)}")


@celery_app.task(
    bind=True,
    name="app.tasks.regenerate_correlations_task",
    max_retries=2,
    default_retry_delay=300,
    acks_late=True,
)
def regenerate_correlations_task(self) -> Dict[str, any]:
    """
    Weekly task to regenerate event-price correlations for all stocks.

    Analyzes historical news events and price movements to update
    correlation data used for predictions.

    Returns:
        Dict with regeneration statistics
    """
    task_id = self.request.id
    db = None

    try:
        logger.info(f"[{task_id}] Starting correlation regeneration")

        from app.models import EventPriceCorrelation

        db = get_db_session()

        # Get all stocks
        stocks = get_tracked_stocks(db)

        if not stocks:
            logger.warning(f"[{task_id}] No stocks found for correlation regeneration")
            return {
                "status": "success",
                "stocks_processed": 0,
                "correlations_updated": 0,
            }

        total_correlations = 0

        for stock_data in stocks:
            stock_id = stock_data["id"]
            ticker = stock_data["ticker"]

            try:
                # Delete existing correlations for this stock
                deleted = db.query(EventPriceCorrelation).filter(
                    EventPriceCorrelation.stock_id == stock_id
                ).delete()

                logger.debug(f"[{task_id}] Deleted {deleted} old correlations for {ticker}")

                # Here you would call the analysis engine to regenerate
                # For now, we log that this would be done
                logger.info(f"[{task_id}] Would regenerate correlations for {ticker}")

                # Placeholder: In full implementation, call analysis engine
                # from app.analysis.analysis_engine import AnalysisEngine
                # engine = AnalysisEngine(db)
                # new_correlations = engine.analyze_stock(stock_id)
                # total_correlations += new_correlations

            except Exception as e:
                logger.error(f"[{task_id}] Error regenerating for {ticker}: {str(e)}")
                continue

        db.commit()

        logger.info(
            f"[{task_id}] Correlation regeneration completed: "
            f"stocks={len(stocks)}, correlations={total_correlations}"
        )

        return {
            "status": "success",
            "stocks_processed": len(stocks),
            "correlations_updated": total_correlations,
        }

    except Exception as e:
        logger.error(f"[{task_id}] Correlation regeneration error: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
        }

    finally:
        if db:
            try:
                db.close()
            except Exception as e:
                logger.warning(f"[{task_id}] Error closing database: {str(e)}")


@celery_app.task(
    bind=True,
    name="app.tasks.check_alerts_task",
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def check_alerts_task(self) -> Dict[str, any]:
    """
    Periodic task to check and trigger alerts.

    Evaluates all active alerts against current stock prices
    and creates triggers when conditions are met.

    Returns:
        Dict with alert check statistics
    """
    task_id = self.request.id
    db = None

    try:
        logger.info(f"[{task_id}] Starting alert check")

        from app.models import Alert, AlertTrigger, AlertStatus, AlertType, StockPrice
        from sqlalchemy import desc

        db = get_db_session()

        # Get all active alerts
        active_alerts = db.query(Alert).filter(
            Alert.status == AlertStatus.ACTIVE,
            Alert.is_enabled == 1,
        ).all()

        if not active_alerts:
            logger.debug(f"[{task_id}] No active alerts to check")
            return {
                "status": "success",
                "alerts_checked": 0,
                "alerts_triggered": 0,
            }

        alerts_triggered = 0

        for alert in active_alerts:
            try:
                # Get latest price for the stock
                latest_price = db.query(StockPrice).filter(
                    StockPrice.stock_id == alert.stock_id
                ).order_by(desc(StockPrice.date)).first()

                if not latest_price or not latest_price.close_price:
                    continue

                current_price = latest_price.close_price
                should_trigger = False
                trigger_message = ""

                # Evaluate alert condition
                if alert.alert_type == AlertType.PRICE_ABOVE:
                    if alert.condition_operator == ">=" and current_price >= alert.condition_value:
                        should_trigger = True
                        trigger_message = f"Price {current_price:.2f} is above {alert.condition_value:.2f}"
                    elif alert.condition_operator == ">" and current_price > alert.condition_value:
                        should_trigger = True
                        trigger_message = f"Price {current_price:.2f} is above {alert.condition_value:.2f}"

                elif alert.alert_type == AlertType.PRICE_BELOW:
                    if alert.condition_operator == "<=" and current_price <= alert.condition_value:
                        should_trigger = True
                        trigger_message = f"Price {current_price:.2f} is below {alert.condition_value:.2f}"
                    elif alert.condition_operator == "<" and current_price < alert.condition_value:
                        should_trigger = True
                        trigger_message = f"Price {current_price:.2f} is below {alert.condition_value:.2f}"

                if should_trigger:
                    # Create trigger record
                    trigger = AlertTrigger(
                        alert_id=alert.id,
                        triggered_value=current_price,
                        message=trigger_message,
                    )
                    db.add(trigger)

                    # Update alert
                    alert.last_triggered_at = datetime.utcnow()
                    alert.status = AlertStatus.TRIGGERED

                    alerts_triggered += 1
                    logger.info(f"[{task_id}] Alert {alert.id} triggered: {trigger_message}")

            except Exception as e:
                logger.error(f"[{task_id}] Error checking alert {alert.id}: {str(e)}")
                continue

        db.commit()

        logger.info(
            f"[{task_id}] Alert check completed: "
            f"checked={len(active_alerts)}, triggered={alerts_triggered}"
        )

        return {
            "status": "success",
            "alerts_checked": len(active_alerts),
            "alerts_triggered": alerts_triggered,
        }

    except Exception as e:
        logger.error(f"[{task_id}] Alert check error: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
        }

    finally:
        if db:
            try:
                db.close()
            except Exception as e:
                logger.warning(f"[{task_id}] Error closing database: {str(e)}")


# =============================================================================
# INTELLIGENT DATA REFRESH TASKS
# Scale-optimized tasks for incremental data updates
# =============================================================================


@celery_app.task(bind=True, name="app.tasks.append_daily_ohlcv_task")
def append_daily_ohlcv_task(self) -> Dict[str, Any]:
    """
    Append today's final OHLCV candle for all tracked stocks.

    Schedule: 4:30 PM IST (Mon-Fri) - 1 hour after NSE market close
    Purpose: Finalize the day's price data without continuous polling

    Returns:
        Dict with status, stocks processed, and any errors
    """
    task_id = self.request.id or "manual"
    logger.info(f"[{task_id}] Starting daily OHLCV append task")

    db: Optional[Session] = None
    results = {
        "status": "success",
        "stocks_processed": 0,
        "stocks_updated": 0,
        "stocks_failed": 0,
        "errors": [],
    }

    try:
        db = SessionLocal()

        # Get all active stocks (NSE/BSE markets)
        stocks = db.query(Stock).filter(
            Stock.market.in_(["NSE", "BSE"]),
            Stock.is_active == True,
        ).all()

        logger.info(f"[{task_id}] Found {len(stocks)} stocks to update")

        for stock in stocks:
            try:
                results["stocks_processed"] += 1

                # Fetch today's OHLCV data
                fetcher = YahooFinanceFetcher(db)
                today = datetime.now().date()

                df = fetcher.fetch_ohlcv(
                    stock.ticker,
                    start_date=datetime.combine(today, datetime.min.time()),
                    end_date=datetime.combine(today, datetime.max.time()),
                )

                if not df.empty:
                    inserted, updated = fetcher.save_to_database(stock.ticker, df)
                    if inserted > 0 or updated > 0:
                        results["stocks_updated"] += 1
                        logger.debug(
                            f"[{task_id}] Updated {stock.ticker}: "
                            f"{inserted} inserted, {updated} updated"
                        )

            except InvalidTickerError as e:
                logger.warning(f"[{task_id}] Invalid ticker {stock.ticker}: {str(e)}")
                results["stocks_failed"] += 1
                results["errors"].append({"ticker": stock.ticker, "error": str(e)})

            except Exception as e:
                logger.error(f"[{task_id}] Error updating {stock.ticker}: {str(e)}")
                results["stocks_failed"] += 1
                results["errors"].append({"ticker": stock.ticker, "error": str(e)})

        logger.info(
            f"[{task_id}] Daily OHLCV append completed: "
            f"processed={results['stocks_processed']}, "
            f"updated={results['stocks_updated']}, "
            f"failed={results['stocks_failed']}"
        )

        return results

    except Exception as e:
        logger.error(f"[{task_id}] Daily OHLCV task error: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
        }

    finally:
        if db:
            try:
                db.close()
            except Exception as e:
                logger.warning(f"[{task_id}] Error closing database: {str(e)}")


@celery_app.task(bind=True, name="app.tasks.refresh_company_info_task")
def refresh_company_info_task(self) -> Dict[str, Any]:
    """
    Refresh company info (metrics, ratios, sector) for all stocks.

    Schedule: 6 AM IST daily - before market opens
    Purpose: Update current metrics like P/E, ROE, ROCE, Market Cap

    Returns:
        Dict with status and update counts
    """
    task_id = self.request.id or "manual"
    logger.info(f"[{task_id}] Starting company info refresh task")

    db: Optional[Session] = None
    results = {
        "status": "success",
        "stocks_processed": 0,
        "stocks_updated": 0,
        "stocks_failed": 0,
        "errors": [],
    }

    try:
        db = SessionLocal()

        # Get all active stocks
        stocks = db.query(Stock).filter(Stock.is_active == True).all()

        logger.info(f"[{task_id}] Found {len(stocks)} stocks for info refresh")

        for stock in stocks:
            try:
                results["stocks_processed"] += 1

                # Use SmartDataManager for info-only sync
                # This updates metrics without re-fetching all historical data
                manager = SmartDataManager(db)
                sync_result = manager.sync_stock(stock.ticker, sync_type=SyncType.PRICE_ONLY)

                if sync_result.get("status") == "success":
                    results["stocks_updated"] += 1

            except Exception as e:
                logger.error(f"[{task_id}] Error refreshing {stock.ticker}: {str(e)}")
                results["stocks_failed"] += 1
                results["errors"].append({"ticker": stock.ticker, "error": str(e)})

        logger.info(
            f"[{task_id}] Company info refresh completed: "
            f"processed={results['stocks_processed']}, "
            f"updated={results['stocks_updated']}, "
            f"failed={results['stocks_failed']}"
        )

        return results

    except Exception as e:
        logger.error(f"[{task_id}] Company info refresh error: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
        }

    finally:
        if db:
            try:
                db.close()
            except Exception as e:
                logger.warning(f"[{task_id}] Error closing database: {str(e)}")


@celery_app.task(bind=True, name="app.tasks.weekly_quarterly_sync_task")
def weekly_quarterly_sync_task(self) -> Dict[str, Any]:
    """
    Check for and fetch new quarterly financial results.

    Schedule: Sunday 2 AM IST
    Purpose: Incrementally sync new quarterly data (not all 13 quarters)

    Returns:
        Dict with status, stocks checked, and quarters fetched
    """
    task_id = self.request.id or "manual"
    logger.info(f"[{task_id}] Starting weekly quarterly sync task")

    db: Optional[Session] = None
    results = {
        "status": "success",
        "stocks_checked": 0,
        "stocks_with_new_data": 0,
        "new_quarters_fetched": 0,
        "errors": [],
    }

    try:
        db = SessionLocal()

        # Get all active stocks
        stocks = db.query(Stock).filter(Stock.is_active == True).all()

        logger.info(f"[{task_id}] Checking {len(stocks)} stocks for new quarterly data")

        for stock in stocks:
            try:
                results["stocks_checked"] += 1

                # Use SmartDataManager with QUARTERLY sync type
                manager = SmartDataManager(db)
                sync_result = manager.sync_stock(stock.ticker, sync_type=SyncType.QUARTERLY)

                if sync_result.get("status") == "success":
                    quarterly_data = sync_result.get("quarterly_results", {})
                    if quarterly_data.get("new_quarters", 0) > 0:
                        results["stocks_with_new_data"] += 1
                        results["new_quarters_fetched"] += quarterly_data["new_quarters"]
                        logger.info(
                            f"[{task_id}] {stock.ticker}: "
                            f"Found {quarterly_data['new_quarters']} new quarters"
                        )

            except Exception as e:
                logger.error(f"[{task_id}] Error syncing {stock.ticker}: {str(e)}")
                results["errors"].append({"ticker": stock.ticker, "error": str(e)})

        logger.info(
            f"[{task_id}] Weekly quarterly sync completed: "
            f"checked={results['stocks_checked']}, "
            f"with_new_data={results['stocks_with_new_data']}, "
            f"new_quarters={results['new_quarters_fetched']}"
        )

        return results

    except Exception as e:
        logger.error(f"[{task_id}] Weekly quarterly sync error: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
        }

    finally:
        if db:
            try:
                db.close()
            except Exception as e:
                logger.warning(f"[{task_id}] Error closing database: {str(e)}")


@celery_app.task(bind=True, name="app.tasks.monthly_annual_sync_task")
def monthly_annual_sync_task(self) -> Dict[str, Any]:
    """
    Check for and fetch new annual financial reports.

    Schedule: 1st of month, 3 AM IST
    Purpose: Incrementally sync new annual data (P&L, balance sheet, cash flow)

    Returns:
        Dict with status, stocks checked, and new annual data count
    """
    task_id = self.request.id or "manual"
    logger.info(f"[{task_id}] Starting monthly annual sync task")

    db: Optional[Session] = None
    results = {
        "status": "success",
        "stocks_checked": 0,
        "stocks_with_new_data": 0,
        "new_annual_reports": 0,
        "errors": [],
    }

    try:
        db = SessionLocal()

        # Get all active stocks
        stocks = db.query(Stock).filter(Stock.is_active == True).all()

        logger.info(f"[{task_id}] Checking {len(stocks)} stocks for new annual data")

        for stock in stocks:
            try:
                results["stocks_checked"] += 1

                # Use SmartDataManager with FULL sync for annual data
                # This checks if new annual reports are available
                manager = SmartDataManager(db)
                sync_result = manager.sync_stock(stock.ticker, sync_type=SyncType.FULL)

                if sync_result.get("status") == "success":
                    annual_data = sync_result.get("annual_results", {})
                    if annual_data.get("new_years", 0) > 0:
                        results["stocks_with_new_data"] += 1
                        results["new_annual_reports"] += annual_data["new_years"]
                        logger.info(
                            f"[{task_id}] {stock.ticker}: "
                            f"Found {annual_data['new_years']} new annual reports"
                        )

            except Exception as e:
                logger.error(f"[{task_id}] Error syncing {stock.ticker}: {str(e)}")
                results["errors"].append({"ticker": stock.ticker, "error": str(e)})

        logger.info(
            f"[{task_id}] Monthly annual sync completed: "
            f"checked={results['stocks_checked']}, "
            f"with_new_data={results['stocks_with_new_data']}, "
            f"new_reports={results['new_annual_reports']}"
        )

        return results

    except Exception as e:
        logger.error(f"[{task_id}] Monthly annual sync error: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
        }

    finally:
        if db:
            try:
                db.close()
            except Exception as e:
                logger.warning(f"[{task_id}] Error closing database: {str(e)}")
