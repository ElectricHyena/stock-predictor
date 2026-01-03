# StockPredictor - Stock Predictability Analysis Platform

A comprehensive platform for analyzing historical stock data to identify predictable patterns and predict future price movements based on news events and market correlations.

## Overview

StockPredictor uses 1+ years of historical stock data combined with news events to:
- Identify which price movements were predictable vs. unpredictable surprises
- Score stocks by their predictability (0-100 score)
- Predict future price movements based on historical event-price correlations
- Provide backtesting capabilities to validate trading strategies

## Tech Stack

### Backend
- **Framework:** FastAPI with async/await
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Cache:** Redis for caching and message broker
- **Background Jobs:** Celery with Redis broker
- **Testing:** pytest with coverage

### Frontend
- **Framework:** Next.js 14 with React 18
- **Language:** TypeScript
- **Styling:** TailwindCSS
- **State Management:** Zustand + TanStack Query
- **UI Components:** shadcn/ui

### DevOps
- **Containerization:** Docker & Docker Compose
- **CI/CD:** GitHub Actions
- **Version Control:** Git

## Quick Start

### Prerequisites
- Docker and Docker Compose (recommended)
- Python 3.10+ (for local development)
- Node.js 18+ (for frontend development)

### Option 1: Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd stock-predictor

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Run database migrations (first time only)
docker-compose exec web alembic upgrade head

# Check service health
docker-compose ps

# View logs
docker-compose logs -f web
```

**Services will be available at:**
- FastAPI Backend: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- API Docs (ReDoc): http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

### Option 2: Local Development

```bash
# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Create database (ensure PostgreSQL is running)
createdb stock_predictor

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Celery worker
celery -A app.tasks worker --loglevel=info
```

## Docker Setup Details

### Services

**postgres** - PostgreSQL 15 database
- User: `dev` (configurable)
- Password: `devpass` (configurable)
- Database: `stock_predictor`
- Port: `5432`

**redis** - Redis 7 cache and message broker
- Port: `6379`

**web** - FastAPI application
- Port: `8000`
- Includes live reload for development
- Health check: `GET /health`

**celery_worker** - Background job processor
- Processes data fetching, analysis, and prediction tasks
- Connects to Redis and PostgreSQL

**celery_beat** - Task scheduler
- Schedules recurring tasks like data updates and analysis

### Environment Configuration

Edit `.env` file to customize:

```env
# FastAPI
DEBUG=True
HOST=0.0.0.0
PORT=8000

# PostgreSQL
POSTGRES_USER=dev
POSTGRES_PASSWORD=devpass
POSTGRES_DB=stock_predictor

# Redis (no auth in default config)
REDIS_PORT=6379

# API Keys
NEWSAPI_KEY=your_newsapi_key_here

# Security
SECRET_KEY=dev-secret-key-change-in-production
```

## Development Workflow

### Running Services

```bash
# Start all services
docker-compose up -d

# Start with verbose logging
docker-compose up

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f [service-name]
```

### Database Migrations

```bash
# Create a new migration
docker-compose exec web alembic revision -m "Description of changes"

# Apply all pending migrations
docker-compose exec web alembic upgrade head

# Rollback one migration
docker-compose exec web alembic downgrade -1

# View migration history
docker-compose exec web alembic history
```

### Testing

```bash
# Run all tests
docker-compose exec web pytest

# Run tests with coverage
docker-compose exec web pytest --cov=app tests/

# Run specific test file
docker-compose exec web pytest tests/test_health.py -v

# Run with verbose output
docker-compose exec web pytest -v
```

### Code Quality

```bash
# Format code
docker-compose exec web black app/

# Check imports
docker-compose exec web isort app/

# Lint code
docker-compose exec web flake8 app/

# Type checking
docker-compose exec web mypy app/
```

## Project Structure

```
stock-predictor/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── main.py          # Application entry point
│   │   ├── config.py        # Configuration management
│   │   ├── database.py      # Database setup
│   │   ├── schemas.py       # Pydantic models
│   │   ├── models/          # SQLAlchemy ORM models
│   │   │   ├── stock.py     # Stock master table
│   │   │   ├── price.py     # Price history
│   │   │   ├── news.py      # News events
│   │   │   ├── correlation.py # Event-price correlations
│   │   │   └── score.py     # Predictability scores
│   │   ├── api/             # API route handlers
│   │   ├── services/        # Business logic
│   │   └── tasks/           # Celery background tasks
│   ├── migrations/          # Alembic database migrations
│   ├── tests/               # Test suite
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile           # Container image definition
│   ├── .dockerignore        # Docker build ignore patterns
│   └── README.md            # Backend-specific docs
├── frontend/                # Next.js frontend (TBD)
├── docker-compose.yml       # Multi-service orchestration
├── .env.example             # Environment variables template
├── .github/workflows/       # CI/CD pipelines
│   └── ci-cd.yml           # GitHub Actions workflow
└── README.md               # This file
```

## Database Schema

### Core Tables

**stocks** - Master stock data
- ticker (unique), company_name, market (NSE/BSE/NYSE), sector, industry
- last_price_updated_at, last_news_updated_at, analysis_status

**stock_prices** - Historical OHLCV data
- Unique constraint on (stock_id, date) prevents duplicates
- Includes calculated fields: daily_return_pct, price_range
- Indexed on: stock_id, date

**news_events** - News articles and events
- event_category (earnings, policy, seasonal, technical, sector)
- sentiment_score, sentiment_category
- content_hash for deduplication (is_duplicate flag)
- Indexed on: stock_id, event_date, event_category, content_hash

**event_price_correlations** - Historical event-price relationships
- Tracks how specific events correlate with price movements
- historical_win_rate, sample_size, confidence_score for pattern strength

**predictability_scores** - Computed predictability metrics
- Overall score (0-100) plus component scores
- current_events, prediction_direction, prediction_magnitude

## API Endpoints

### Health & Status
- `GET /` - API info and documentation links
- `GET /health` - Health check endpoint

### Stock Data (Phase 2 - TBD)
- `GET /stocks/search?q=` - Search stocks by symbol/name
- `GET /stocks/{ticker}` - Get stock details and predictability
- `GET /stocks/{ticker}/prices` - Historical price data
- `GET /stocks/{ticker}/news` - Related news events

### Analysis (Phase 3 - TBD)
- `GET /stocks/{ticker}/predictability` - Predictability score
- `GET /stocks/{ticker}/prediction` - Price movement prediction
- `POST /stocks/{ticker}/backtest` - Test trading strategy
- `GET /stocks/{ticker}/analysis` - Full analysis report

## CI/CD Pipeline

The project includes a comprehensive GitHub Actions workflow that:

1. **Runs Tests** - pytest with coverage reporting
2. **Checks Code Quality** - flake8, mypy, black, isort
3. **Builds Docker Image** - Multi-stage build for production
4. **Security Scanning** - Trivy vulnerability scanner
5. **Verifies Docker Compose** - Tests full service health

Workflow runs on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

## Troubleshooting

### Services won't start
```bash
# Check service logs
docker-compose logs postgres
docker-compose logs redis
docker-compose logs web

# Verify port availability
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # API
```

### Database connection errors
```bash
# Check PostgreSQL is healthy
docker-compose exec postgres pg_isready -U dev

# View database logs
docker-compose logs postgres

# Reset database
docker-compose down -v  # Remove volumes
docker-compose up -d postgres
docker-compose exec web alembic upgrade head
```

### API not responding
```bash
# Check API logs
docker-compose logs -f web

# Test health endpoint
curl http://localhost:8000/health

# Check if port is in use
lsof -i :8000
```

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and test: `docker-compose exec web pytest`
3. Run code quality checks: `docker-compose exec web black app/`
4. Commit with clear message: `git commit -m "feat: description"`
5. Push and create a pull request

## Development Roadmap

### Phase 1: Foundation ✅ (In Progress)
- [x] Project Infrastructure
- [x] Database Schema & Migrations
- [ ] Data Fetchers (Yahoo Finance, NewsAPI)
- [ ] Celery Background Tasks

### Phase 2: API Endpoints (TBD)
- Pydantic Schemas
- RESTful endpoints for stock search, details, predictions

### Phase 3: Analysis Engine (TBD)
- Event categorization
- Sentiment analysis
- Correlation analysis
- Predictability scoring

### Phase 4: Frontend MVP (TBD)
- Frontend setup with Next.js
- Search and discovery page
- Stock detail page with predictability card

### Phase 5: Advanced Features (TBD)
- Historical analysis page
- Backtest builder and results
- Watchlist and alerts

### Phase 6: Polish & Deployment (TBD)
- Error handling and validation
- Rate limiting and caching
- Monitoring and logging
- Production deployment

## License

Proprietary - StockPredictor

## Contact & Support

For issues, questions, or contributions, please create an issue in the repository.

---

**Last Updated:** January 3, 2026
**Status:** Foundation Phase (In Progress)
**Latest Version:** 0.1.0
