# StockPredictor Backend

FastAPI-based backend for the StockPredictor platform.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application entry point
│   ├── config.py         # Settings and environment variables
│   ├── database.py       # Database configuration
│   ├── schemas.py        # Pydantic models
│   ├── models/           # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── stock.py
│   │   ├── price.py
│   │   ├── news.py
│   │   ├── correlation.py
│   │   └── score.py
│   ├── api/              # API routes (to be created)
│   ├── services/         # Business logic (to be created)
│   └── tasks/            # Celery tasks (to be created)
├── tests/                # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   └── test_*.py
├── migrations/           # Alembic database migrations (to be created)
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore patterns
├── pytest.ini           # Pytest configuration
└── README.md            # This file
```

## Setup

### Option 1: Docker Setup (Recommended)

```bash
# From project root directory
docker-compose up -d

# Run migrations (first time only)
docker-compose exec web alembic upgrade head

# Check services are running
docker-compose ps

# View logs
docker-compose logs -f web
```

**Available at:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Option 2: Local Development Setup

#### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
```

#### 3. Initialize Database

```bash
# Create database (PostgreSQL must be running)
createdb stock_predictor

# Run migrations
alembic upgrade head
```

#### 4. Run Development Server

```bash
# Start FastAPI server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Celery worker
celery -A app.tasks worker --loglevel=info

# Optionally, start Celery beat for scheduled tasks
celery -A app.tasks beat --loglevel=info
```

Visit:
- API: http://localhost:8000
- Docs (Swagger): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

## Development

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_health.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black app/

# Check imports
isort app/

# Lint
flake8 app/

# Type checking
mypy app/
```

## API Documentation

Once running, visit `/docs` for interactive Swagger documentation or `/redoc` for ReDoc documentation.

## Database Models

### Stock
Master table for stocks

### StockPrice
Historical OHLCV data

### NewsEvent
News articles and events

### EventPriceCorrelation
Historical correlations between events and price movements

### PredictabilityScore
Computed predictability scores

## Technologies

- **Framework:** FastAPI
- **Database:** PostgreSQL + SQLAlchemy
- **Async:** asyncio + uvicorn
- **Background Jobs:** Celery + Redis
- **Testing:** pytest
- **Data:** pandas, numpy, scikit-learn

## Docker Commands

### Service Management

```bash
# Start services in background
docker-compose up -d

# Start with verbose logging
docker-compose up

# Stop all services
docker-compose down

# Restart services
docker-compose restart

# View service status
docker-compose ps

# View logs
docker-compose logs -f [service-name]

# Execute command in service
docker-compose exec web pytest
```

### Database Migrations in Docker

```bash
# Run pending migrations
docker-compose exec web alembic upgrade head

# Create new migration
docker-compose exec web alembic revision -m "description"

# Rollback one migration
docker-compose exec web alembic downgrade -1

# View migration history
docker-compose exec web alembic history
```

### Common Issues

**Services won't start:**
```bash
# Check port availability
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # API

# Kill process on port (if necessary)
kill -9 $(lsof -ti:8000)
```

**Database connection errors:**
```bash
# Check PostgreSQL health
docker-compose exec postgres pg_isready -U dev

# View database logs
docker-compose logs postgres

# Reset database (WARNING: deletes data)
docker-compose down -v
docker-compose up -d postgres
docker-compose exec web alembic upgrade head
```

**API not responding:**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Check API logs
docker-compose logs -f web

# Rebuild image (if changed)
docker-compose build web
docker-compose up -d web
```

## Next Steps

1. ✅ Set up database migrations (Alembic) - DONE
2. Create API routes (Phase 2)
3. Implement data fetching services (Phase 1)
4. Implement analysis engine (Phase 3)
5. Set up background tasks (Celery) - partially done
6. Add authentication (Phase 6)
7. Write comprehensive tests (Phase 6)

## Contributing

Follow the structure and patterns established in this project.

1. Create feature branch
2. Make changes
3. Run tests and linting
4. Create pull request

## License

Proprietary - StockPredictor
