# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**StockPredictor** is a full-stack platform for analyzing historical stock data to identify predictable patterns and predict future price movements. It combines historical price data with news events to score stocks by predictability and provide price forecasts.

**Tech Stack:**
- Backend: FastAPI (Python 3.10+) with PostgreSQL, Redis, Celery
- Frontend: Next.js 14 (React 18, TypeScript, TailwindCSS)
- DevOps: Docker Compose, GitHub Actions CI/CD
- Testing: pytest with coverage (80% minimum)

**Current Phase:** Phase 1.5 Complete - Infrastructure, database, data fetchers, and intelligent refresh strategy implemented. Frontend MVP functional.

## Key Architecture

### Database Schema

The database contains 5 core tables with a precise schema design:

- **stocks**: Master table (ticker PK, company_name, market, sector, industry, is_active for enable/disable)
- **stock_prices**: Historical OHLCV data indexed on (stock_id, date), includes daily_return_pct and price_range
- **news_events**: News articles with event_category, sentiment_score, content_hash for dedup, indexed on category and date
- **event_price_correlations**: Historical event-price relationships tracked with win_rate and confidence_score
- **predictability_scores**: Computed scores (0-100) plus component metrics (events, direction, magnitude)

Schema uses Alembic for migrations. Foreign keys enforce referential integrity. Deduplication via content_hash prevents duplicate news ingestion.

### Backend Structure

```
backend/app/
├── main.py              # FastAPI app factory, middleware (CORS, logging), health/root endpoints
├── config.py            # Settings from .env (pydantic-settings), builds DATABASE_URL
├── database.py          # SQLAlchemy engine, session factory, declarative base
├── schemas.py           # Pydantic v2 models for request/response validation
├── models/              # SQLAlchemy ORM models (stock, price, news, correlation, score, user)
├── api/                 # Route handlers organized by resource (stocks, analysis, backtest, etc.)
├── services/            # Business logic (data fetching, analysis, predictions)
├── analysis/            # ML/analysis engine (event categorization, sentiment, correlations)
├── middleware/          # Custom middleware (request logging, error handling)
├── tasks.py             # Celery task definitions and execution
├── cache.py             # Redis caching layer with TTLs
├── rate_limiter.py      # Rate limiting implementation
├── exceptions.py        # Custom exception classes
├── health.py            # Health check utilities
├── logging_config.py    # Structured logging setup
└── validators.py        # Input validation functions
```

Key patterns:
- All routes return JSON with consistent response format
- Services decouple business logic from HTTP handlers
- Tasks run asynchronously via Celery (data fetching, analysis, background work)
- Cache layer for expensive operations (sentiment, predictions)

### Docker Architecture

Services defined in `docker-compose.yml`:
- **postgres**: PostgreSQL 15 (port 5432 via POSTGRES_PORT env var)
- **redis**: Redis 7 (port 6379 via REDIS_PORT env var)
- **web**: FastAPI (port 8000 via API_PORT env var, hot-reload enabled)
- **celery_worker**: Background task processor
- **celery_beat**: Task scheduler for periodic jobs

Services communicate internally via service names (e.g., `postgres:5432`). Ports are configurable via `.env` to prevent conflicts.

## Common Development Commands

### Docker-Based Workflow (Recommended)

```bash
# Start all services
docker-compose up -d

# Run tests
docker-compose exec web pytest
docker-compose exec web pytest tests/test_health.py -v       # Single file
docker-compose exec web pytest --cov=app tests/             # With coverage

# Database migrations
docker-compose exec web alembic upgrade head                 # Apply migrations
docker-compose exec web alembic revision -m "Description"    # Create migration
docker-compose exec web alembic downgrade -1                 # Rollback one

# Code quality
docker-compose exec web black app/                            # Format
docker-compose exec web isort app/                            # Import sort
docker-compose exec web flake8 app/                           # Lint
docker-compose exec web mypy app/                             # Type check

# Logs & debug
docker-compose logs -f web                                   # API logs
docker-compose logs -f celery_worker                        # Task worker logs
docker-compose ps                                            # Service status
```

### Local Development Setup

```bash
# Setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Create and migrate database (PostgreSQL must be running)
createdb stock_predictor
alembic upgrade head

# Run server (with hot reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Celery worker
celery -A app.tasks worker --loglevel=info

# Tests
pytest                                                       # All tests
pytest tests/test_health.py -v                              # Single file
pytest --cov=app tests/ -v                                   # With coverage
```

## Database & Migrations

**Alembic** manages schema changes. Migrations are in `backend/migrations/versions/`.

Creating migrations:
```bash
docker-compose exec web alembic revision -m "Add column X to table Y"
# Edit the created migration file in migrations/versions/
# Add upgrade() and downgrade() logic with raw SQL
docker-compose exec web alembic upgrade head  # Apply
```

**Important:** Migrations use raw SQLAlchemy SQL expressions, not ORM. Foreign key constraints are enforced. Test all migrations locally before merging.

## Environment Configuration

`.env` file (copy from `.env.example`):

```env
# FastAPI
DEBUG=True
HOST=0.0.0.0
API_PORT=8000

# PostgreSQL (service name is "postgres")
POSTGRES_USER=dev
POSTGRES_PASSWORD=devpass
POSTGRES_DB=stock_predictor
POSTGRES_PORT=5432

# Redis
REDIS_PORT=6379

# API Keys
NEWSAPI_KEY=your_api_key_here

# Security
SECRET_KEY=dev-secret-key-change-in-production
```

**Port Conflict Resolution:** If ports are in use, modify `.env` and restart:
```bash
# .env
POSTGRES_PORT=5433
REDIS_PORT=6380
API_PORT=8001

docker-compose down && docker-compose up -d
```

## Testing Standards

**Requirements:**
- Minimum coverage: 80% (enforced in `pytest.ini`)
- Test file pattern: `tests/test_*.py`
- Test class pattern: `Test*`
- Test function pattern: `test_*`

**Test markers** (in `pytest.ini`):
- `@pytest.mark.unit` - Fast, isolated tests
- `@pytest.mark.integration` - Database/service tests
- `@pytest.mark.e2e` - Full system tests
- `@pytest.mark.slow` - Slow tests run separately

Run markers:
```bash
pytest -m unit                    # Only unit tests
pytest -m "integration or e2e"   # Integration + E2E
pytest -m "not slow"             # Skip slow tests
```

Configuration in `conftest.py` provides fixtures (db session, mock services, test client).

## Code Quality Checklist

Before committing:

1. **Format:** `black app/` - Auto-formats code to PEP 8
2. **Imports:** `isort app/` - Sorts imports, removes unused
3. **Lint:** `flake8 app/` - Catches style issues and common errors
4. **Type Check:** `mypy app/` - Validates type annotations
5. **Tests:** `pytest --cov=app tests/` - Must pass with ≥80% coverage

All tools are in `requirements.txt`. GitHub Actions CI runs these on every push/PR.

## Celery Tasks Architecture

Tasks are defined in `backend/app/tasks.py` and use Redis as broker:

```python
from app.celery_config import app as celery_app

@celery_app.task(bind=True)
def my_task(self, param):
    # Long-running work here
    return result
```

**Key patterns:**
- Use `bind=True` to access task context (retry, ID tracking)
- Return serializable data (JSON-safe)
- Database queries inside tasks should create new sessions
- Use `.delay()` or `.apply_async()` to enqueue

**Celery beat** (scheduler) config is in `celery_beat_schedule.py`. Periodic tasks run on defined intervals (e.g., fetch data every 15 minutes).

Celery result backend is Redis. Monitor with:
```bash
celery -A app.tasks events  # Real-time event monitor
```

## Pydantic Model Patterns

Uses Pydantic v2 (see `schemas.py`):

```python
from pydantic import BaseModel, Field, validator

class StockRequest(BaseModel):
    ticker: str = Field(..., min_length=1)
    market: str = "NYSE"

    @field_validator('ticker')
    @classmethod
    def ticker_uppercase(cls, v):
        return v.upper()

class StockResponse(BaseModel):
    id: int
    ticker: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # For ORM
```

All request/response models inherit from `BaseModel`. Use `Field` for documentation and validation. ORM objects use `model_config = ConfigDict(from_attributes=True)` to work with SQLAlchemy.

## Error Handling

Custom exceptions in `backend/app/exceptions.py`. HTTP error responses are standardized:

```python
from app.exceptions import ValidationError, NotFoundError

# In route handler
if not stock:
    raise NotFoundError(f"Stock {ticker} not found")

# Response format
{
    "detail": "Stock UNKNOWN not found",
    "error_code": "NOT_FOUND",
    "timestamp": "2026-01-03T14:00:00Z"
}
```

Handlers in `main.py` catch exceptions and return JSON. Never let raw exceptions escape to the client.

## Cache Strategy

Redis caching via `backend/app/cache.py`:

```python
from app.cache import cache_manager

# Set with TTL
cache_manager.set("stock:AAPL", data, ttl=3600)

# Get
data = cache_manager.get("stock:AAPL")

# Delete
cache_manager.delete("stock:AAPL")
```

Cache keys follow pattern: `{resource}:{id}:{variant}`. TTLs are tuned per resource type. Cache invalidation happens after data updates.

## API Response Structure

Responses follow consistent JSON structure:

```json
{
    "status": "success",
    "data": { ... },
    "meta": {
        "timestamp": "2026-01-03T14:00:00Z",
        "version": "0.2.0"
    }
}
```

Error responses:
```json
{
    "status": "error",
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input",
        "details": [...]
    }
}
```

## Rate Limiting

`backend/app/rate_limiter.py` implements token-bucket rate limiting. Applied via middleware.

```bash
# Usage: tracked per IP, returns 429 if exceeded
GET /api/stocks  # Rate limit: 100 req/min
```

Configure limits per endpoint in API router.

## Data Architecture (Generic & Extensible)

The system is **fully generic** - no hardcoded stock tickers. All stocks are dynamically fetched from the database. To add a new stock:

1. Insert into `stocks` table via API (`POST /api/stocks`)
2. Set `is_active = True` to include in automated syncs
3. Celery tasks automatically pick up new stocks on next scheduled run

### Data Sources

| Source | Data Provided | Update Frequency |
|--------|---------------|------------------|
| **Screener.in** | Company info, financials, ratios, quarterly/annual results | Daily (fundamentals) |
| **Yahoo Finance** | Real-time prices, OHLCV history, dividends, splits | Every 15 min (market hours) |
| **NewsAPI** | News articles, headlines, sentiment analysis | Every 30 min |

### Intelligent Refresh Strategy

Located in `backend/app/services/smart_data_manager.py`:

```python
# Sync types with different data requirements
full_sync()       # All data - new stocks or weekly refresh
price_sync()      # Prices only - every 15 min during market hours
quarterly_sync()  # Quarterly financials - after earnings (Jan, Apr, Jul, Oct)
annual_sync()     # Annual financials - post fiscal year (Apr-May for India)
```

**Celery Beat Schedule** (`celery_beat_schedule.py`):
- `price-sync`: Every 15 min, Mon-Fri, 9:15 AM - 3:30 PM IST
- `daily-sync`: 6 AM daily (company info, news)
- `quarterly-sync`: 1st of Jan, Apr, Jul, Oct
- `annual-sync`: April 15th yearly
- `weekly-full-sync`: Sundays at 2 AM

### Key Services

| Service | Purpose | Location |
|---------|---------|----------|
| `SmartDataManager` | Orchestrates all data syncs | `services/smart_data_manager.py` |
| `HybridFetcher` | Combines Screener + Yahoo data | `services/hybrid_fetcher.py` |
| `ScreenerScraper` | Scrapes Screener.in for fundamentals | `services/screener_scraper.py` |
| `FinancialFetcher` | Yahoo Finance wrapper | `services/financial_fetcher.py` |
| `DataFetchers` | Legacy data fetching | `services/data_fetchers.py` |

## Next Steps (Roadmap)

- ~~Phase 1.5: Data fetchers + Celery tasks~~ ✅ Complete
- Phase 2: Analysis engine (event categorization, sentiment, correlation)
- Phase 3: Predictability scoring algorithm
- Phase 4: Backtesting framework

## Important Files by Task

| Task | Key Files |
|------|-----------|
| Add API endpoint | `api/router.py`, `schemas.py` |
| Add database model | `models/*.py`, create migration |
| Add background task | `tasks.py`, `celery_beat_schedule.py` |
| Add test | `tests/test_*.py`, `conftest.py` |
| Update config | `config.py`, `.env.example` |
| Fix migration | `migrations/versions/*.py` |
| Implement service logic | `services/*.py` |
| Add new data source | `services/`, update `HybridFetcher` |
| Modify refresh schedule | `celery_beat_schedule.py` |

## Testing Patterns & Gotchas

### Cache Isolation in Tests

The `conftest.py` clears Redis cache before/after each test to prevent test pollution:

```python
@pytest.fixture(scope="function")
def client(db: Session):
    # Clear cache before test
    from app.cache import cache
    cache.clear()

    with TestClient(app) as test_client:
        yield test_client

    # Clear cache after test
    cache.clear()
```

**Important:** If tests fail with stale data, check cache isolation first.

### Migration Naming Convention

Alembic revisions use simple numeric IDs:
- ✅ Correct: `revision = '006'`, `down_revision = '005'`
- ❌ Wrong: `revision = '006_add_column'`, `down_revision = '005_something'`

## Port Configuration

Default ports (configurable via `.env`):

| Service | Default Port | Env Variable |
|---------|--------------|--------------|
| Backend API | 7000 | `API_PORT` |
| Frontend | 7004 | (in package.json) |
| PostgreSQL | 5432 | `POSTGRES_PORT` |
| Redis | 6379 | `REDIS_PORT` |

## Documentation

- **System Architecture**: `docs/system-architecture.html` - Interactive HTML explaining full system
- **API Docs**: `http://localhost:7000/docs` (Swagger UI)
- **This file**: Development guidance for Claude Code

