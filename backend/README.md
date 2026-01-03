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

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
```

### 3. Initialize Database

```bash
# Create database (PostgreSQL)
createdb stock_predictor

# Run migrations (when available)
alembic upgrade head
```

### 4. Run Development Server

```bash
# Start FastAPI server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
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

## Next Steps

1. Set up database migrations (Alembic)
2. Create API routes
3. Implement data fetching services
4. Implement analysis engine
5. Set up background tasks (Celery)
6. Add authentication
7. Write comprehensive tests

## Contributing

Follow the structure and patterns established in this project.

1. Create feature branch
2. Make changes
3. Run tests and linting
4. Create pull request

## License

Proprietary - StockPredictor
