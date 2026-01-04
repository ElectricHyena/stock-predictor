"""
Backtest API Endpoint
STORY_2_7: Backtest endpoint for validating trading strategies
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, List
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app import models, schemas
from app.cache import cache, cache_key_backtest, CACHE_TTL_BACKTEST

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backtest", tags=["backtest"])


class BacktestEngine:
    """Engine for running backtest simulations"""

    def __init__(self, db: Session):
        self.db = db

    def run_backtest(self, request: schemas.BacktestRequest) -> schemas.BacktestResult:
        """
        Run a backtest for given strategy and ticker

        Returns:
            BacktestResult with performance metrics and trade list
        """
        # Get stock
        stock = self.db.query(models.Stock).filter(
            models.Stock.ticker == request.ticker.upper()
        ).first()

        if not stock:
            raise ValueError(f"Stock {request.ticker} not found")

        # Get price data for date range
        prices = self.db.query(models.StockPrice).filter(
            and_(
                models.StockPrice.stock_id == stock.id,
                models.StockPrice.date >= request.start_date,
                models.StockPrice.date <= request.end_date,
            )
        ).order_by(models.StockPrice.date.asc()).all()

        if not prices:
            raise ValueError(f"No price data found for {request.ticker} in date range")

        # Initialize backtest state
        capital = request.initial_capital
        position_size = 0
        entry_price = 0.0
        entry_date = None
        trades: List[schemas.BacktestTrade] = []
        equity_curve: List[float] = [capital]
        dates: List[date] = []

        # Process each price point
        for i, price_point in enumerate(prices):
            current_date = price_point.date
            current_price = price_point.close_price or price_point.open_price or 0

            if current_price == 0:
                continue

            # Check entry signal
            if position_size == 0:
                # Evaluate entry signal
                if self._evaluate_signal(request.strategy.entry_signal, price_point, stock):
                    # Enter position
                    position_size = int(request.initial_capital * request.strategy.position_size / current_price)
                    entry_price = current_price
                    entry_date = current_date
                    capital -= position_size * current_price * (1 + request.slippage_pct / 100)
                    logger.debug(f"Opened position: {position_size} shares at {entry_price}")

            # Check exit signal
            elif position_size > 0:
                should_exit = False
                exit_signal_name = "none"

                # Check stop loss
                if request.strategy.stop_loss_pct:
                    loss_pct = (current_price - entry_price) / entry_price * 100
                    if loss_pct <= -request.strategy.stop_loss_pct:
                        should_exit = True
                        exit_signal_name = "stop_loss"

                # Check take profit
                elif request.strategy.take_profit_pct:
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    if profit_pct >= request.strategy.take_profit_pct:
                        should_exit = True
                        exit_signal_name = "take_profit"

                # Check exit signal
                elif self._evaluate_signal(request.strategy.exit_signal, price_point, stock):
                    should_exit = True
                    exit_signal_name = request.strategy.exit_signal

                # Check max holding days
                if (current_date - entry_date).days >= (request.strategy.max_holding_days or 999):
                    should_exit = True
                    exit_signal_name = "max_holding_days"

                # Execute exit
                if should_exit:
                    exit_price = current_price
                    profit = position_size * (exit_price - entry_price)
                    profit -= position_size * exit_price * (request.slippage_pct / 100)  # Slippage
                    profit -= position_size * exit_price * 0.001  # Commission (0.1%)

                    capital += position_size * exit_price * (1 - request.slippage_pct / 100)
                    return_pct = ((exit_price - entry_price) / entry_price) * 100

                    trade = schemas.BacktestTrade(
                        entry_date=entry_date,
                        exit_date=current_date,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        quantity=position_size,
                        return_pct=return_pct,
                        entry_signal=request.strategy.entry_signal,
                        exit_signal=exit_signal_name,
                    )
                    trades.append(trade)

                    position_size = 0
                    entry_price = 0.0
                    entry_date = None

                    logger.debug(f"Closed position: {return_pct:.2f}% return")

            # Record equity point
            open_position_value = position_size * current_price if position_size > 0 else 0
            total_equity = capital + open_position_value
            equity_curve.append(total_equity)
            dates.append(current_date)

        # Close any open position at end
        if position_size > 0 and len(prices) > 0:
            final_price = prices[-1].close_price or prices[-1].open_price or 0
            if final_price > 0:
                capital += position_size * final_price * (1 - request.slippage_pct / 100)
                return_pct = ((final_price - entry_price) / entry_price) * 100
                trade = schemas.BacktestTrade(
                    entry_date=entry_date,
                    exit_date=prices[-1].date,
                    entry_price=entry_price,
                    exit_price=final_price,
                    quantity=position_size,
                    return_pct=return_pct,
                    entry_signal=request.strategy.entry_signal,
                    exit_signal="end_of_period",
                )
                trades.append(trade)

        # Calculate metrics
        total_return = (capital - request.initial_capital) / request.initial_capital * 100
        winning_trades = sum(1 for t in trades if t.return_pct and t.return_pct > 0)
        losing_trades = len(trades) - winning_trades
        win_rate = winning_trades / len(trades) if trades else 0

        avg_win = sum(t.return_pct for t in trades if t.return_pct and t.return_pct > 0) / winning_trades if winning_trades > 0 else 0
        avg_loss = sum(t.return_pct for t in trades if t.return_pct and t.return_pct <= 0) / losing_trades if losing_trades > 0 else 0

        # Calculate max drawdown
        max_equity = equity_curve[0]
        max_drawdown = 0.0
        for equity in equity_curve:
            if equity > max_equity:
                max_equity = equity
            drawdown = (max_equity - equity) / max_equity if max_equity > 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # Calculate Sharpe ratio (simplified, assuming risk-free rate = 0)
        if len(equity_curve) > 1:
            returns = [(equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1] for i in range(1, len(equity_curve))]
            avg_return = sum(returns) / len(returns) if returns else 0
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns) if returns else 0
            std_dev = variance ** 0.5
            sharpe_ratio = (avg_return * 252) / (std_dev * (252 ** 0.5)) if std_dev > 0 else 0
        else:
            sharpe_ratio = 0.0

        # Calculate profit factor
        total_wins = sum(t.return_pct for t in trades if t.return_pct and t.return_pct > 0) or 0.01
        total_losses = abs(sum(t.return_pct for t in trades if t.return_pct and t.return_pct <= 0)) or 0.01
        profit_factor = total_wins / total_losses if total_losses > 0 else 0

        # Create metrics
        metrics = [
            schemas.BacktestMetric(name="Total Return", value=total_return, unit="%"),
            schemas.BacktestMetric(name="Win Rate", value=win_rate * 100, unit="%"),
            schemas.BacktestMetric(name="Max Drawdown", value=max_drawdown * 100, unit="%"),
            schemas.BacktestMetric(name="Sharpe Ratio", value=sharpe_ratio),
            schemas.BacktestMetric(name="Profit Factor", value=profit_factor),
        ]

        result = schemas.BacktestResult(
            ticker=request.ticker.upper(),
            strategy_name=request.strategy.name,
            backtest_period_start=request.start_date,
            backtest_period_end=request.end_date,
            initial_capital=request.initial_capital,
            final_capital=capital,
            total_return_pct=total_return,
            num_trades=len(trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win_pct=avg_win,
            avg_loss_pct=avg_loss,
            max_drawdown_pct=max_drawdown * 100,
            sharpe_ratio=sharpe_ratio,
            profit_factor=profit_factor,
            trades=trades,
            metrics=metrics,
        )

        return result

    def _evaluate_signal(self, signal: str, price_point: models.StockPrice, stock: models.Stock) -> bool:
        """
        Evaluate if a signal is triggered

        Simple implementation - can be extended with more complex rules
        """
        signal_lower = signal.lower()

        # Simple signal evaluation
        if "close_above" in signal_lower:
            # Placeholder: would need additional context
            return True
        elif "close_below" in signal_lower:
            return True
        elif "volume_increase" in signal_lower:
            return True
        elif "volatility_high" in signal_lower:
            return True

        return False


# ============================================================================
# STORY_2_7: Backtest Endpoint
# ============================================================================

@router.post("", response_model=schemas.BacktestResponse)
async def run_backtest(
    request: schemas.BacktestRequest,
    db: Session = Depends(get_db),
):
    """
    Run a backtest for a trading strategy (STORY_2_7)

    Request Body:
    - ticker: Stock ticker symbol
    - start_date: Backtest start date
    - end_date: Backtest end date
    - initial_capital: Starting capital (default 10000)
    - strategy: BacktestStrategy with entry/exit signals
    - use_leverage: Enable leverage (default false)
    - max_leverage: Max leverage multiplier (default 1.0)
    - include_slippage: Include slippage in calculations (default true)
    - slippage_pct: Slippage percentage (default 0.1%)

    Returns:
    - BacktestResponse with results, metrics, and trade list
    """
    try:
        # Check cache
        cache_key = cache_key_backtest(request.ticker, request.strategy.name)
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for backtest: {request.ticker}")
            return schemas.BacktestResponse(
                status="completed",
                result=schemas.BacktestResult(**cached_result),
            )

        # Run backtest
        engine = BacktestEngine(db)
        result = engine.run_backtest(request)

        response = schemas.BacktestResponse(
            status="completed",
            result=result,
        )

        # Cache results
        cache.set(cache_key, result.model_dump(mode='json'), CACHE_TTL_BACKTEST)
        logger.info(f"Backtest completed: {request.ticker}, win_rate={result.win_rate:.2%}")

        return response

    except ValueError as e:
        logger.error(f"Backtest validation error: {e}")
        return schemas.BacktestResponse(
            status="error",
            error=str(e),
        )
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        return schemas.BacktestResponse(
            status="error",
            error="Backtest failed: " + str(e),
        )


@router.post("/async", response_model=dict)
async def run_backtest_async(
    request: schemas.BacktestRequest,
    db: Session = Depends(get_db),
):
    """
    Run a backtest asynchronously using Celery.

    Returns a task_id that can be used to check the result later.

    Request Body:
    - Same as POST /backtest

    Returns:
    - task_id: ID to track the backtest job
    - status: "queued"
    """
    try:
        from app.tasks import run_backtest_task

        # Queue the backtest task
        task = run_backtest_task.delay(
            ticker=request.ticker,
            start_date=request.start_date.isoformat(),
            end_date=request.end_date.isoformat(),
            initial_capital=request.initial_capital,
            strategy_name=request.strategy.name,
            entry_signal=request.strategy.entry_signal,
            exit_signal=request.strategy.exit_signal,
            position_size=request.strategy.position_size,
            stop_loss_pct=request.strategy.stop_loss_pct,
            take_profit_pct=request.strategy.take_profit_pct,
            max_holding_days=request.strategy.max_holding_days,
            slippage_pct=request.slippage_pct,
        )

        logger.info(f"Queued async backtest: task_id={task.id}, ticker={request.ticker}")

        return {
            "task_id": task.id,
            "status": "queued",
            "message": f"Backtest for {request.ticker} queued. Check /backtests/{task.id} for results.",
        }

    except Exception as e:
        logger.error(f"Failed to queue backtest: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to queue backtest: {str(e)}")


@router.get("/{run_id}", response_model=schemas.BacktestResponse)
async def get_backtest_result(run_id: str, db: Session = Depends(get_db)):
    """
    Retrieve backtest results by run ID.

    Returns the status and results of an async backtest job.

    Path Parameters:
    - run_id: The task ID returned from POST /backtests/async

    Returns:
    - BacktestResponse with status and results (if completed)
    """
    try:
        from celery.result import AsyncResult
        from app.celery_config import celery_app

        logger.info(f"Retrieving backtest result: {run_id}")

        # Get task result
        result = AsyncResult(run_id, app=celery_app)

        if result.state == "PENDING":
            return schemas.BacktestResponse(
                status="pending",
                error="Backtest job is still queued or does not exist",
            )
        elif result.state == "STARTED":
            return schemas.BacktestResponse(
                status="processing",
                error="Backtest job is currently running",
            )
        elif result.state == "SUCCESS":
            task_result = result.get()

            if task_result.get("status") == "completed" and task_result.get("result"):
                return schemas.BacktestResponse(
                    status="completed",
                    result=schemas.BacktestResult(**task_result["result"]),
                )
            else:
                return schemas.BacktestResponse(
                    status="failed",
                    error=task_result.get("error", "Unknown error"),
                )
        elif result.state == "FAILURE":
            return schemas.BacktestResponse(
                status="failed",
                error=str(result.result),
            )
        else:
            return schemas.BacktestResponse(
                status=result.state.lower(),
                error=f"Backtest in state: {result.state}",
            )

    except Exception as e:
        logger.error(f"Get backtest result error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve backtest results")
