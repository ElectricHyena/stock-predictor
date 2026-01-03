---
# Backtest Endpoint

**Story ID:** STORY_2_7
**Phase:** 2 (API Endpoints)
**Story Points:** 8
**Status:** Not Started

## User Story
**As a** frontend developer
**I want** users to backtest trading strategies against historical data
**So that** they can validate if their patterns actually work before trading real money

## Acceptance Criteria
- [ ] POST /backtest/run accepts strategy rules and backtests them
- [ ] Returns backtest results: win rate, total P&L, Sharpe ratio, max drawdown
- [ ] Returns trade-by-trade breakdown with entry/exit prices and dates
- [ ] Returns warnings about potential overfitting risks
- [ ] Async execution with polling endpoint to check status
- [ ] GET /backtest/{run_id} retrieves completed results
- [ ] Strategy supports conditions on predictability score, information availability, win rate
- [ ] Backtest handles commission costs and slippage
- [ ] Results are stored in database for audit trail
- [ ] Supports date range customization for backtesting period

## Implementation Tasks
- [ ] Create `POST /backtest/run` endpoint to accept strategy rules
- [ ] Build rule engine to evaluate conditions against historical data
- [ ] Implement trade simulation logic against price history
- [ ] Calculate P&L for each trade (commission-adjusted)
- [ ] Calculate performance metrics: win rate, total P&L, Sharpe ratio, max drawdown
- [ ] Create trade-by-trade breakdown response
- [ ] Implement overfitting detection and warnings
- [ ] Create Celery task for async backtest execution
- [ ] Implement `GET /backtest/{run_id}` polling endpoint
- [ ] Store backtest runs and results in database
- [ ] Add validation for strategy rules
- [ ] Write comprehensive unit tests
- [ ] Write integration tests for the endpoint
- [ ] Document strategy rule syntax
- [ ] Add performance optimization for large backtests

## Test Cases
- [ ] Backtest runs successfully for valid strategy
- [ ] Backtest calculates P&L correctly (verified manually)
- [ ] Backtest returns all required metrics
- [ ] Trade list includes all trades with correct entry/exit prices
- [ ] Polling endpoint correctly returns in-progress status
- [ ] Polling endpoint returns completed results
- [ ] Overfitting warning triggered for high-frequency, low-volume strategies
- [ ] Commission costs reduce P&L correctly
- [ ] Max drawdown calculation is accurate
- [ ] Sharpe ratio calculation follows standard formula
- [ ] Invalid strategy rules return helpful error messages
- [ ] Results persist across server restarts

## Dependencies
- STORY_1_2 (Database Schema)
- STORY_1_3 (Data Fetcher Service)
- STORY_2_1 (Pydantic Schemas)
- STORY_3_3 (Event-Price Correlation Analysis)
- STORY_3_4 (Predictability Scoring Algorithm)

## Notes
- Async execution critical for large backtests (may take minutes)
- Use Celery tasks with Redis for job queue
- Implement pagination for trade lists (100 trades per page)
- Store all backtests for audit and comparison
- Support conditions: predictability_score >= X, information_available, win_rate >= Y
- Include position sizing options (fixed size, percentage of capital)
- Calculate Sharpe ratio with risk-free rate = 0%
- Detect overfitting: if trades < 10 or trade frequency > 50% of days
- Commission: 0.1% per trade by default
- Slippage: 0.05% per trade by default
- Support S&P 500 assumption for benchmark Sharpe calculation

---
