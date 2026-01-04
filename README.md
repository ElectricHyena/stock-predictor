# StockPredictor

Full-stack stock analysis and prediction platform with ML-based predictability scoring, technical indicators, backtesting, and alert systems.

![Build Status](https://github.com/ElectricHyena/stock-predictor/actions/workflows/ci-cd.yml/badge.svg)

## Features

- **Stock Search & Analysis** - Search stocks, view historical data with technical indicators (RSI, MACD, SMA, EMA)
- **Predictability Scoring** - ML-based scoring analyzing price patterns, volatility, and correlations
- **Backtesting Engine** - Build and test trading strategies with equity curve visualization
- **Watchlist Management** - Track favorite stocks with portfolio insights
- **Alert System** - Price alerts, prediction changes, volume spikes with notifications
- **News Integration** - Real-time news sentiment analysis via NewsAPI

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, SQLAlchemy, PostgreSQL, Celery, Redis |
| Frontend | Next.js 14, React Query, Recharts, Tailwind CSS |
| Data | Yahoo Finance API, NewsAPI |
| Infrastructure | Docker, Docker Compose, GitHub Actions CI/CD |

## Quick Start

### Prerequisites

- Docker & Docker Compose (recommended)
- Or: Python 3.10+, Node.js 18+, PostgreSQL 14+, Redis 7+

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/ElectricHyena/stock-predictor.git
cd stock-predictor

# Copy environment files
cp .env.example .env

# Edit .env with your API keys (NEWSAPI_KEY required)
# Get one free at https://newsapi.org

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Check health
curl http://localhost:8000/health
```

**Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs

### Option 2: Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with DATABASE_URL, REDIS_URL, NEWSAPI_KEY

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev
```

#### Celery Workers (background tasks)

```bash
cd backend

# Worker (processes tasks)
celery -A app.celery_config worker --loglevel=info

# Beat (scheduled tasks - alerts, data refresh)
celery -A app.celery_config beat --loglevel=info
```

## Environment Variables

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/stock_predictor

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys
NEWSAPI_KEY=your_newsapi_key_here

# Security
SECRET_KEY=your-secret-key-here
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/stocks/search` | GET | Search stocks by query |
| `/api/v1/stocks/{ticker}` | GET | Get stock details |
| `/api/v1/stocks/{ticker}/historical` | GET | Historical price data |
| `/api/v1/stocks/{ticker}/analysis` | GET | Predictability analysis |
| `/api/v1/backtests` | POST | Run backtest simulation |
| `/api/v1/backtests/{id}` | GET | Get backtest results |
| `/api/v1/watchlists` | GET/POST | Manage watchlists |
| `/api/v1/alerts` | GET/POST | Manage price alerts |
| `/health` | GET | Health check |

Full API documentation at `/docs` when running the backend.

## Project Structure

```
stock-predictor/
├── backend/
│   ├── app/
│   │   ├── api/           # API routes (stocks, backtest, alerts, watchlist)
│   │   ├── analysis/      # ML modules (predictor, sentiment, correlator)
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── services/      # Data fetchers (Yahoo Finance, NewsAPI)
│   │   ├── middleware/    # Error handling
│   │   ├── tasks.py       # Celery background tasks
│   │   └── schemas.py     # Pydantic request/response schemas
│   ├── migrations/        # Alembic database migrations
│   └── tests/             # 242 pytest tests
├── frontend/
│   ├── app/               # Next.js 14 app router (11 routes)
│   ├── components/        # React components (charts, forms, tables)
│   └── lib/               # API client, utilities
├── docs/
│   ├── API.md
│   └── ARCHITECTURE.md
└── docker-compose.yml
```

## Running Tests

### Backend (242 tests)

```bash
cd backend
pytest -v                    # Run all tests
pytest --cov=app            # With coverage report
pytest -k "test_api"        # Run specific tests
```

### Frontend

```bash
cd frontend
npm run build              # Type check and build
npm test                   # Run Jest tests (if configured)
```

## Technical Indicators

The platform calculates these indicators client-side for real-time charting:

- **RSI (14)** - Relative Strength Index with overbought/oversold zones
- **MACD (12, 26, 9)** - Moving Average Convergence Divergence with signal line
- **SMA 20** - Simple Moving Average
- **EMA 12** - Exponential Moving Average

## Development

### Adding a New API Endpoint

1. Create route in `backend/app/api/`
2. Add Pydantic schemas in `backend/app/schemas.py`
3. Register router in `backend/app/api/router.py`
4. Write tests in `backend/tests/`

### Adding a New Frontend Page

1. Create page in `frontend/app/`
2. Add components in `frontend/components/`
3. Use React Query hooks for data fetching

## Deployment Checklist

- [ ] Set secure `SECRET_KEY` in production
- [ ] Configure production `DATABASE_URL`
- [ ] Set up Redis for production
- [ ] Add `NEWSAPI_KEY` to environment
- [ ] Enable HTTPS
- [ ] Configure CORS for your domain

## License

MIT

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest -v`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

---

**Status:** All 5 phases complete | 242 backend tests passing | 11 frontend routes
