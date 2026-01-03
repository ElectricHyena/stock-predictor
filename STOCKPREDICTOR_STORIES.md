# StockPredictor - User Stories & Tasks

## Overview
Complete breakdown of all user stories needed to build StockPredictor MVP. Each story includes acceptance criteria, implementation tasks, and test cases.

---

## PHASE 1: FOUNDATION (Weeks 1-2)

### STORY 1.1: Project Infrastructure Setup
**As a** developer
**I want** a properly structured project with Docker and CI/CD
**So that** the team can develop and deploy consistently

**Acceptance Criteria:**
- [ ] Backend and frontend directories created with proper structure
- [ ] Docker Compose file sets up postgres, redis, backend, frontend
- [ ] GitHub Actions CI pipeline runs tests on push
- [ ] All services start cleanly with `docker-compose up`

**Tasks:**
- [ ] Create backend directory structure: `app/`, `tests/`, `migrations/`, `config/`
- [ ] Create frontend directory structure: `app/`, `components/`, `services/`, `hooks/`, `types/`
- [ ] Initialize FastAPI backend with main.py
- [ ] Initialize Next.js frontend
- [ ] Create docker-compose.yml with all 4 services (postgres, redis, backend, frontend)
- [ ] Create .github/workflows/ci.yml for automated tests
- [ ] Create docker-compose.override.yml for local development
- [ ] Document setup instructions in README.md

**Test Cases:**
- [ ] `docker-compose up` successfully starts all services
- [ ] Backend /health endpoint returns 200 OK
- [ ] Frontend loads at localhost:3000
- [ ] PostgreSQL is accessible at localhost:5432
- [ ] Redis is accessible at localhost:6379

**Story Points:** 5

---

### STORY 1.2: Database Schema & Migrations
**As a** data engineer
**I want** a well-designed PostgreSQL schema with migrations
**So that** data is stored consistently and can be versioned

**Acceptance Criteria:**
- [ ] All 8 tables created with proper relationships
- [ ] Alembic migrations set up and versioned
- [ ] Indexes created for performance
- [ ] Unique constraints prevent duplicates
- [ ] Migrations can be rolled back cleanly

**Tasks:**
- [ ] Configure Alembic for database versioning
- [ ] Create Stock table with indexes on ticker and market
- [ ] Create StockPrice table with composite key on (stock_id, date)
- [ ] Create NewsEvent table with event_date and category indexes
- [ ] Create EventPriceCorrelation table for analysis results
- [ ] Create PredictabilityScore table for caching scores
- [ ] Create BacktestRun and BacktestTrade tables
- [ ] Create User, Watchlist, Alert tables
- [ ] Create PipelineJob and ApiAuditLog tables
- [ ] Write first migration and test rollback
- [ ] Document schema in docs/DATABASE.md

**Test Cases:**
- [ ] `alembic upgrade head` succeeds without errors
- [ ] All tables exist in database
- [ ] Composite key (stock_id, date) prevents duplicate prices
- [ ] Foreign keys enforce referential integrity
- [ ] Indexes can be queried efficiently
- [ ] `alembic downgrade base` succeeds

**Story Points:** 8

---

### STORY 1.3: Data Fetcher Service - Yahoo Finance Integration
**As a** data engineer
**I want** to automatically fetch historical price data from Yahoo Finance
**So that** the system has accurate OHLCV data for analysis

**Acceptance Criteria:**
- [ ] Fetcher downloads 1+ year of data for any NSE/BSE stock
- [ ] Data is normalized (trading days only, returns calculated)
- [ ] Handles missing data gracefully
- [ ] Handles rate limiting and retries
- [ ] Tests mock Yahoo Finance API

**Tasks:**
- [ ] Create `services/data_fetcher.py` with `DataFetcher` class
- [ ] Implement `fetch_stock_prices(ticker, days)` method
- [ ] Add data normalization: trading day alignment, return calculation
- [ ] Add error handling and retry logic (3 attempts, exponential backoff)
- [ ] Create unit tests with mocked yfinance
- [ ] Add integration test with real ticker (AVANTIFEED.NS)
- [ ] Document API in docstrings

**Test Cases:**
- [ ] Test fetch returns OHLCV data for valid ticker
- [ ] Test handles invalid ticker gracefully
- [ ] Test calculates daily returns correctly
- [ ] Test skips weekends/holidays
- [ ] Test retries on network failure
- [ ] Test returns [] on persistent failure

**Story Points:** 5

---

### STORY 1.4: News Fetcher Service - NewsAPI Integration
**As a** data engineer
**I want** to automatically fetch news articles about stocks
**So that** the system can correlate news with price movements

**Acceptance Criteria:**
- [ ] Fetches articles from NewsAPI for any stock
- [ ] Deduplicates articles (content hash)
- [ ] Categorizes articles by type (earnings, policy, etc)
- [ ] Calculates sentiment score
- [ ] Handles API rate limits

**Tasks:**
- [ ] Implement `fetch_news(ticker, days)` in DataFetcher
- [ ] Add article deduplication by content hash
- [ ] Create `categorize_event(headline, content)` method
- [ ] Create `calculate_sentiment(text)` method
- [ ] Add error handling for API failures
- [ ] Create unit tests with mocked requests
- [ ] Document news categories in docs/NEWS_CATEGORIES.md

**Test Cases:**
- [ ] Test fetches articles for valid ticker
- [ ] Test deduplicates same article from multiple sources
- [ ] Test categorizes earnings news correctly
- [ ] Test categorizes policy news correctly
- [ ] Test sentiment is between -1 and +1
- [ ] Test handles API key missing gracefully

**Story Points:** 5

---

### STORY 1.5: Celery Tasks for Background Data Fetching
**As a** backend developer
**I want** background jobs to fetch and store prices/news daily
**So that** data is kept fresh without blocking API requests

**Acceptance Criteria:**
- [ ] Celery tasks fetch prices and store in DB daily
- [ ] Celery tasks fetch news and store in DB daily
- [ ] Tasks are scheduled using Celery Beat
- [ ] Failed tasks are logged and alertable
- [ ] Tasks are idempotent (safe to retry)

**Tasks:**
- [ ] Set up Celery with Redis broker
- [ ] Create `fetch_prices_task(ticker)` in tasks.py
- [ ] Create `fetch_news_task(ticker)` in tasks.py
- [ ] Make tasks idempotent (check before inserting)
- [ ] Set up Celery Beat scheduler for 9:35 PM IST (prices) and every 2 hours (news)
- [ ] Add logging for task execution
- [ ] Create unit tests for tasks
- [ ] Document task scheduling in docs/CELERY_TASKS.md

**Test Cases:**
- [ ] Task successfully fetches and stores prices
- [ ] Task doesn't create duplicate prices on retry
- [ ] Task logs success/failure
- [ ] Task handles database errors gracefully
- [ ] Celery Beat triggers tasks on schedule

**Story Points:** 6

---

## PHASE 2: API ENDPOINTS (Weeks 3-4)

### STORY 2.1: Pydantic Schemas for Request/Response
**As a** API developer
**I want** strongly-typed request/response schemas
**So that** the API is self-documenting and validated

**Acceptance Criteria:**
- [ ] All API models defined in schemas.py
- [ ] Schemas use Pydantic for validation
- [ ] Schemas include examples in docstrings
- [ ] Response models match frontend expectations

**Tasks:**
- [ ] Create StockBase, StockResponse schemas
- [ ] Create PriceData, NewsEventResponse schemas
- [ ] Create PredictabilityScoreResponse schema
- [ ] Create PredictionResponse schema
- [ ] Create BacktestRequest, BacktestResult schemas
- [ ] Create Alert, Watchlist schemas
- [ ] Add example() methods to schemas
- [ ] Document all schemas in docs/API_SCHEMAS.md

**Test Cases:**
- [ ] Schema validates correct data
- [ ] Schema rejects invalid data with helpful error
- [ ] Schema converts types correctly
- [ ] Schema.model_validate_json works

**Story Points:** 3

---

### STORY 2.2: Stock Search & Discovery Endpoint
**As a** frontend developer
**I want** to search for stocks by ticker or name
**So that** users can find stocks to analyze

**Acceptance Criteria:**
- [ ] GET /stocks/search?q=AVANTI&market=NSE returns matching stocks
- [ ] Returns max 10 results by default
- [ ] Results include ticker, name, current price, analysis status
- [ ] Searches are case-insensitive
- [ ] Handles market filtering (NSE, BSE, NYSE)

**Tasks:**
- [ ] Create `stocks.py` router
- [ ] Implement `GET /stocks/search` endpoint
- [ ] Add database query for ticker/name fuzzy search
- [ ] Add market filtering
- [ ] Add pagination (limit, offset)
- [ ] Add tests for various search queries
- [ ] Document endpoint in docs/API.md

**Test Cases:**
- [ ] Search finds stock by exact ticker
- [ ] Search finds stock by partial name
- [ ] Search is case-insensitive
- [ ] Search respects market filter
- [ ] Search returns empty list for no matches
- [ ] Search handles special characters safely

**Story Points:** 3

---

### STORY 2.3: Stock Detail Endpoint
**As a** frontend developer
**I want** to get detailed info about a specific stock
**So that** I can display it on the stock detail page

**Acceptance Criteria:**
- [ ] GET /stocks/{ticker} returns stock details
- [ ] Creates stock in DB if not exists
- [ ] Triggers async price/news fetch
- [ ] Returns current price, last updated times
- [ ] Handles unknown tickers gracefully

**Tasks:**
- [ ] Implement `GET /stocks/{ticker}` endpoint
- [ ] Auto-create stock if not found
- [ ] Trigger async data fetch tasks
- [ ] Return stock details + metadata
- [ ] Add error handling for invalid tickers
- [ ] Write tests

**Test Cases:**
- [ ] Known stock returns correct data
- [ ] Unknown stock is created and fetch triggered
- [ ] Stock data is returned as expected schema

**Story Points:** 2

---

### STORY 2.4: Predictability Score Endpoint
**As a** frontend developer
**I want** to get the current predictability score for a stock
**So that** I can display it prominently on the UI

**Acceptance Criteria:**
- [ ] GET /stocks/{ticker}/predictability-score returns score
- [ ] Score is 0-100 integer
- [ ] Returns 4 sub-scores (info, pattern, timing, direction)
- [ ] Returns confidence level
- [ ] Returns trading recommendation (TRADE_THIS, MAYBE, AVOID)

**Tasks:**
- [ ] Implement `GET /stocks/{ticker}/predictability-score` endpoint
- [ ] Call analysis engine to compute score
- [ ] Cache score in Redis for 5 minutes
- [ ] Return score with breakdown
- [ ] Add tests

**Test Cases:**
- [ ] Endpoint returns score 0-100
- [ ] Endpoint returns 4 sub-scores
- [ ] Endpoint returns confidence 0-1
- [ ] Endpoint caches in Redis

**Story Points:** 3

---

### STORY 2.5: Prediction Endpoint
**As a** frontend developer
**I want** to get current prediction (direction, magnitude, timing)
**So that** I can show users what move is expected

**Acceptance Criteria:**
- [ ] GET /stocks/{ticker}/prediction returns direction and magnitude
- [ ] Direction is UP/DOWN
- [ ] Magnitude is "+2% to +4%" format
- [ ] Timing is same-day/next-day/lagged
- [ ] Returns historical win rate

**Tasks:**
- [ ] Implement `GET /stocks/{ticker}/prediction` endpoint
- [ ] Call prediction service
- [ ] Format response user-friendly
- [ ] Add tests

**Test Cases:**
- [ ] Endpoint returns valid direction
- [ ] Endpoint returns magnitude range
- [ ] Endpoint returns timing

**Story Points:** 2

---

### STORY 2.6: Historical Analysis Endpoint
**As a** frontend developer
**I want** to get 1-year historical analysis for a stock
**So that** users can see what was predictable in the past

**Acceptance Criteria:**
- [ ] GET /stocks/{ticker}/historical-analysis returns 1-year data
- [ ] Returns price performance stats (total return, wins, losses, volatility)
- [ ] Returns predictability breakdown (60% predictable, 40% unpredictable)
- [ ] Returns event-by-event analysis
- [ ] Returns key insights

**Tasks:**
- [ ] Implement `GET /stocks/{ticker}/historical-analysis` endpoint
- [ ] Calculate price performance stats
- [ ] Analyze event correlations
- [ ] Classify events as predictable/unpredictable
- [ ] Generate insights
- [ ] Add tests

**Test Cases:**
- [ ] Endpoint returns correct date range
- [ ] Endpoint calculates returns correctly
- [ ] Endpoint returns predictability %

**Story Points:** 5

---

### STORY 2.7: Backtest Endpoint
**As a** frontend developer
**I want** users to backtest trading strategies
**So that** they can validate if patterns actually work

**Acceptance Criteria:**
- [ ] POST /backtest/run accepts strategy rules
- [ ] Returns backtest results: win rate, P&L, Sharpe ratio
- [ ] Returns trade-by-trade breakdown
- [ ] Returns warnings about overfitting
- [ ] Async execution with polling

**Tasks:**
- [ ] Implement `POST /backtest/run` endpoint
- [ ] Build rule engine for strategy evaluation
- [ ] Simulate trades against historical data
- [ ] Calculate P&L and metrics
- [ ] Store results in database
- [ ] Implement polling for async results
- [ ] Add tests

**Test Cases:**
- [ ] Backtest runs successfully
- [ ] Backtest calculates P&L correctly
- [ ] Backtest returns all metrics
- [ ] Can poll for results

**Story Points:** 8

---

## PHASE 3: ANALYSIS ENGINE (Weeks 3-4)

### STORY 3.1: Event Categorization Engine
**As a** data scientist
**I want** to categorize all news events into types
**So that** I can analyze patterns by event type

**Acceptance Criteria:**
- [ ] Events categorized as: earnings, policy, seasonal, technical, sector
- [ ] Categorization is rule-based and deterministic
- [ ] High accuracy (>90%) on test set
- [ ] Fast categorization (<100ms per article)

**Tasks:**
- [ ] Create categorization rules based on keywords
- [ ] Implement in `services/analysis_engine.py`
- [ ] Build test set of 100+ articles
- [ ] Measure accuracy
- [ ] Optimize for speed
- [ ] Document rules in docs/CATEGORIZATION_RULES.md

**Test Cases:**
- [ ] Earnings news categorized as earnings
- [ ] Policy news categorized as policy
- [ ] Holiday news categorized as seasonal
- [ ] Unknown news categorized as sector

**Story Points:** 3

---

### STORY 3.2: Sentiment Analysis
**As a** data scientist
**I want** to calculate sentiment for each news article
**So that** I can correlate sentiment with price movements

**Acceptance Criteria:**
- [ ] Sentiment score is -1 to +1
- [ ] Positive words increase score
- [ ] Negative words decrease score
- [ ] Neutral articles score near 0
- [ ] Fast calculation (<50ms per article)

**Tasks:**
- [ ] Implement simple lexicon-based sentiment in DataFetcher
- [ ] Build positive/negative word lists
- [ ] Test on sample articles
- [ ] Document word lists
- [ ] Consider TextBlob/VADER for better accuracy

**Test Cases:**
- [ ] Positive words score > 0.5
- [ ] Negative words score < -0.5
- [ ] Neutral articles score -0.2 to +0.2

**Story Points:** 2

---

### STORY 3.3: Event-Price Correlation Analysis
**As a** data scientist
**I want** to correlate past events with price moves
**So that** I can build predictive patterns

**Acceptance Criteria:**
- [ ] Analyze historical correlation for each event type
- [ ] Calculate: occurrences, avg move, win rate, timing
- [ ] Store results in EventPriceCorrelation table
- [ ] Regenerate correlations weekly
- [ ] Results feed into predictability scoring

**Tasks:**
- [ ] Create `analyze_event_correlation()` method
- [ ] Query all events and corresponding price moves
- [ ] Calculate statistics per event category
- [ ] Store in database
- [ ] Add Celery task to recalculate weekly
- [ ] Add tests

**Test Cases:**
- [ ] Correlation analysis finds historical patterns
- [ ] Win rates are accurate (verified manually)
- [ ] Results stored in database

**Story Points:** 5

---

### STORY 3.4: Predictability Scoring Algorithm
**As a** data scientist
**I want** to score predictability of each event type
**So that** users know which patterns to trade

**Acceptance Criteria:**
- [ ] Score is 0-100 integer
- [ ] Weighted average of 4 factors (info, pattern, timing, direction)
- [ ] Weights: 30% info, 25% pattern, 25% timing, 20% direction
- [ ] Fast calculation (<200ms)

**Tasks:**
- [ ] Implement `calculate_predictability_score()` method
- [ ] Implement 4 scoring methods for each factor
- [ ] Aggregate with weights
- [ ] Cache results
- [ ] Add tests with known scores
- [ ] Document scoring logic in docs/SCORING.md

**Test Cases:**
- [ ] High info availability increases score
- [ ] High win rate increases score
- [ ] Immediate timing increases score
- [ ] Final score is weighted correctly
- [ ] Score is always 0-100

**Story Points:** 5

---

## PHASE 4: FRONTEND MVP (Weeks 5-6)

### STORY 4.1: Frontend Project Setup & Layout
**As a** frontend developer
**I want** Next.js 14 project with TailwindCSS and base layout
**So that** I can build pages quickly

**Acceptance Criteria:**
- [ ] Next.js 14 with App Router initialized
- [ ] TailwindCSS configured
- [ ] Base layout with navbar and sidebar
- [ ] Authentication pages (login/signup) created
- [ ] Responsive design (mobile, tablet, desktop)

**Tasks:**
- [ ] Initialize Next.js 14 with create-next-app
- [ ] Install and configure TailwindCSS
- [ ] Install shadcn/ui components
- [ ] Create base layout component with navbar
- [ ] Create auth pages (placeholder)
- [ ] Add responsive design breakpoints
- [ ] Document setup in docs/FRONTEND_SETUP.md

**Test Cases:**
- [ ] App loads at localhost:3000
- [ ] Layout displays correctly on mobile
- [ ] Layout displays correctly on desktop
- [ ] Navbar is visible on all pages

**Story Points:** 3

---

### STORY 4.2: API Client Service Layer
**As a** frontend developer
**I want** typed API client with React Query
**So that** data fetching is consistent and cached

**Acceptance Criteria:**
- [ ] Axios client configured with base URL
- [ ] React Query hooks for each endpoint
- [ ] Type-safe requests and responses
- [ ] Automatic retry and error handling
- [ ] Request interceptor adds auth token

**Tasks:**
- [ ] Create `services/api.ts` with axios client
- [ ] Create `services/stockService.ts` with stock endpoints
- [ ] Create `services/predictionService.ts`
- [ ] Create `services/backtestService.ts`
- [ ] Create custom React Query hooks
- [ ] Add error handling
- [ ] Add tests

**Test Cases:**
- [ ] API client makes requests to correct URL
- [ ] React Query caches responses
- [ ] Errors are handled gracefully
- [ ] Auth token is sent in headers

**Story Points:** 4

---

### STORY 4.3: Stock Search & Discovery Page
**As a** user
**I want** to search for stocks and see predictability scores
**So that** I can find interesting stocks to analyze

**Acceptance Criteria:**
- [ ] Search box to enter stock ticker
- [ ] Market selector (NSE, BSE, NYSE)
- [ ] Results show stock cards with predictability scores
- [ ] Color-coded ratings (green > 75, yellow 50-75, red < 50)
- [ ] Click to navigate to stock detail page

**Tasks:**
- [ ] Create `app/dashboard/page.tsx`
- [ ] Create `components/dashboard/StockSearch.tsx`
- [ ] Create `components/dashboard/StockCard.tsx`
- [ ] Integrate with stockService.search()
- [ ] Add debouncing to search input
- [ ] Style with TailwindCSS
- [ ] Add loading and error states
- [ ] Add tests

**Test Cases:**
- [ ] Search works for valid ticker
- [ ] Results display predictability score
- [ ] Cards show green/yellow/red correctly
- [ ] Click navigates to detail page

**Story Points:** 5

---

### STORY 4.4: Stock Detail Page Layout
**As a** user
**I want** to see stock details including current price
**So that** I have context about the stock

**Acceptance Criteria:**
- [ ] Page shows stock ticker and company name
- [ ] Displays current price
- [ ] Shows 52-week high/low
- [ ] Shows market cap
- [ ] Shows last updated timestamp
- [ ] Layout is clean and organized

**Tasks:**
- [ ] Create `app/dashboard/[ticker]/page.tsx`
- [ ] Create `components/stock-detail/PriceHeader.tsx`
- [ ] Fetch stock data on page load
- [ ] Display price and metrics
- [ ] Add loading state
- [ ] Add error state
- [ ] Add tests

**Test Cases:**
- [ ] Page loads for valid ticker
- [ ] Price updates in real-time
- [ ] All metrics display correctly

**Story Points:** 3

---

### STORY 4.5: Predictability Score Card Component
**As a** user
**I want** to see the predictability score prominently
**So that** I immediately know if this stock is tradeable

**Acceptance Criteria:**
- [ ] Large circular gauge showing 0-100 score
- [ ] Color-coded: green > 75, yellow 50-75, red < 50
- [ ] Shows 4 sub-scores (info, pattern, timing, direction)
- [ ] Shows confidence level
- [ ] Shows recommendation text

**Tasks:**
- [ ] Create `components/stock-detail/PredictabilityCard.tsx`
- [ ] Implement SVG gauge chart or use Chart.js
- [ ] Fetch predictability score from API
- [ ] Display recommendation text
- [ ] Add loading and error states
- [ ] Style with gradients
- [ ] Add tests

**Test Cases:**
- [ ] Card displays score 0-100
- [ ] Card shows correct color for score
- [ ] Sub-scores display correctly

**Story Points:** 4

---

### STORY 4.6: Prediction Banner Component
**As a** user
**I want** to see what move is predicted today
**So that** I know the immediate trading opportunity

**Acceptance Criteria:**
- [ ] Shows predicted direction (UP/DOWN)
- [ ] Shows expected move magnitude
- [ ] Shows timing (same-day, next-day, lagged)
- [ ] Shows historical win rate
- [ ] Shows reasoning

**Tasks:**
- [ ] Create `components/stock-detail/PredictionBanner.tsx`
- [ ] Fetch prediction from API
- [ ] Display direction with arrow icon
- [ ] Show magnitude range
- [ ] Show win rate percentage
- [ ] Style based on direction (green for UP, red for DOWN)
- [ ] Add tests

**Test Cases:**
- [ ] Banner shows correct direction
- [ ] Win rate displays as percentage
- [ ] Colors match direction

**Story Points:** 3

---

## PHASE 5: ADVANCED FEATURES (Weeks 7-10)

### STORY 5.1: Historical Analysis Page
**As a** user
**I want** to see event-by-event analysis of what was predictable
**So that** I learn which patterns actually work

**Acceptance Criteria:**
- [ ] Page shows 1-year price performance
- [ ] Event timeline showing each major event
- [ ] Color-coded: green = predictable, red = unpredictable
- [ ] Shows 4 sub-scores for each event
- [ ] Shows whether prediction was correct
- [ ] Shows key insights

**Tasks:**
- [ ] Create `app/dashboard/[ticker]/historical/page.tsx`
- [ ] Create `components/analysis/EventTimeline.tsx`
- [ ] Fetch historical analysis from API
- [ ] Build event timeline component
- [ ] Color code events
- [ ] Display prediction accuracy
- [ ] Add tests

**Test Cases:**
- [ ] Page loads historical data
- [ ] Events display in chronological order
- [ ] Colors match predictability

**Story Points:** 6

---

### STORY 5.2: Backtest Strategy Builder
**As a** user
**I want** to create trading rules and backtest them
**So that** I can validate my trading ideas

**Acceptance Criteria:**
- [ ] Rule builder UI with conditions
- [ ] Rules: predictability score ≥ X, information available, win rate ≥ Y
- [ ] Entry/exit options
- [ ] Position size input
- [ ] Date range selector
- [ ] "Run Backtest" button

**Tasks:**
- [ ] Create `app/dashboard/[ticker]/backtest/page.tsx`
- [ ] Create `components/backtest/StrategyBuilder.tsx`
- [ ] Build rule builder UI with react-hook-form
- [ ] Validate rules
- [ ] Send to API
- [ ] Show loading state
- [ ] Add tests

**Test Cases:**
- [ ] Builder validates required fields
- [ ] Can submit valid strategy
- [ ] Shows errors for invalid rules

**Story Points:** 5

---

### STORY 5.3: Backtest Results Display
**As a** user
**I want** to see detailed backtest results
**So that** I understand how my strategy would have performed

**Acceptance Criteria:**
- [ ] Summary metrics: total trades, win rate, P&L, Sharpe ratio
- [ ] Trade-by-trade breakdown
- [ ] Entry/exit prices and dates
- [ ] P&L for each trade
- [ ] Warnings about overfitting
- [ ] Export to CSV option

**Tasks:**
- [ ] Create `components/backtest/BacktestResults.tsx`
- [ ] Create `components/backtest/TradeList.tsx`
- [ ] Fetch results from API
- [ ] Display summary metrics
- [ ] Display trade list with pagination
- [ ] Add warnings
- [ ] Add export button
- [ ] Add tests

**Test Cases:**
- [ ] Results display correctly
- [ ] Trade list shows all trades
- [ ] Metrics calculate correctly

**Story Points:** 5

---

### STORY 5.4: Watchlist Feature
**As a** user
**I want** to save stocks to a watchlist
**So that** I can track my favorite stocks

**Acceptance Criteria:**
- [ ] Add/remove from watchlist button
- [ ] Watchlist page showing all saved stocks
- [ ] Sort by predictability score
- [ ] Delete from watchlist
- [ ] Persisted in database

**Tasks:**
- [ ] Create watchlist endpoint (POST /user/watchlist)
- [ ] Create remove endpoint (DELETE /user/watchlist/{id})
- [ ] Create list endpoint (GET /user/watchlist)
- [ ] Create `components/stock-detail/WatchlistButton.tsx`
- [ ] Create `app/dashboard/watchlist/page.tsx`
- [ ] Add mutation hooks
- [ ] Add tests

**Test Cases:**
- [ ] Can add stock to watchlist
- [ ] Can remove stock from watchlist
- [ ] Watchlist persists across sessions
- [ ] Watchlist page loads correctly

**Story Points:** 4

---

### STORY 5.5: Alert System
**As a** user
**I want** to set alerts for high predictability events
**So that** I'm notified when to trade

**Acceptance Criteria:**
- [ ] Set alert threshold (e.g., score > 75)
- [ ] Choose notification method (email, webhook)
- [ ] Alert fires when condition met
- [ ] User can view alert history
- [ ] Can enable/disable alerts

**Tasks:**
- [ ] Create alert endpoints (POST, GET, PUT, DELETE)
- [ ] Create `components/stock-detail/AlertButton.tsx`
- [ ] Create alert management page
- [ ] Implement alert trigger logic
- [ ] Send email notifications (email service integration)
- [ ] Add tests

**Test Cases:**
- [ ] Can create alert
- [ ] Alert fires when condition met
- [ ] Can disable alert
- [ ] Email sent correctly

**Story Points:** 6

---

## PHASE 6: POLISH & DEPLOYMENT (Weeks 11-12)

### STORY 6.1: Error Handling & Validation
**As a** developer
**I want** comprehensive error handling
**So that** users get helpful error messages

**Acceptance Criteria:**
- [ ] API errors return 400/401/404/500 with clear messages
- [ ] Frontend shows user-friendly error messages
- [ ] Validation errors explain what's wrong
- [ ] Errors are logged for debugging
- [ ] Graceful degradation on failures

**Tasks:**
- [ ] Create error handling middleware
- [ ] Add try-catch to all API routes
- [ ] Add form validation with react-hook-form
- [ ] Create error boundary component
- [ ] Add error logging to backend
- [ ] Test all error scenarios

**Test Cases:**
- [ ] Invalid input returns 400 with message
- [ ] Unauthorized access returns 401
- [ ] Not found returns 404
- [ ] Server error returns 500 with logging

**Story Points:** 5

---

### STORY 6.2: Rate Limiting & Caching
**As a** developer
**I want** rate limiting to prevent abuse
**So that** the API is stable and costs are controlled

**Acceptance Criteria:**
- [ ] API limited to 100 requests/minute per user
- [ ] Predictability scores cached 5 minutes
- [ ] Historical data cached 1 hour
- [ ] Price data cached 15 minutes
- [ ] Clear cache button for admin

**Tasks:**
- [ ] Implement rate limiting middleware
- [ ] Add Redis caching layer
- [ ] Cache predictability scores
- [ ] Cache historical analysis
- [ ] Set cache TTLs
- [ ] Add cache invalidation on data updates
- [ ] Test rate limiting

**Test Cases:**
- [ ] Requests over limit rejected with 429
- [ ] Cached data returned within TTL
- [ ] Cache invalidated on update

**Story Points:** 4

---

### STORY 6.3: Monitoring & Logging
**As a** ops engineer
**I want** comprehensive logging and monitoring
**So that** I can debug issues in production

**Acceptance Criteria:**
- [ ] All requests logged with timestamp, endpoint, status
- [ ] All errors logged with stack trace
- [ ] Performance metrics logged (response time)
- [ ] Background job status logged
- [ ] Database query logging for debugging

**Tasks:**
- [ ] Add structured logging with Python logging module
- [ ] Add request/response logging middleware
- [ ] Add error logging with context
- [ ] Add performance monitoring
- [ ] Set up log aggregation
- [ ] Create dashboards (Grafana/CloudWatch)
- [ ] Test logging

**Test Cases:**
- [ ] Requests are logged
- [ ] Errors are logged with stack trace
- [ ] Performance metrics are captured

**Story Points:** 4

---

### STORY 6.4: Documentation
**As a** user or developer
**I want** comprehensive documentation
**So that** I can understand and extend the system

**Acceptance Criteria:**
- [ ] API documentation (Swagger)
- [ ] Architecture guide
- [ ] Setup instructions
- [ ] Deployment guide
- [ ] Contributing guide
- [ ] Troubleshooting guide

**Tasks:**
- [ ] Generate Swagger/OpenAPI docs from FastAPI
- [ ] Write architecture.md explaining system design
- [ ] Write SETUP.md with detailed instructions
- [ ] Write DEPLOY.md for production deployment
- [ ] Write CONTRIBUTING.md for developers
- [ ] Write TROUBLESHOOTING.md for common issues
- [ ] Add code comments where needed

**Test Cases:**
- [ ] All endpoints documented in Swagger
- [ ] README is complete and accurate

**Story Points:** 5

---

### STORY 6.5: Deployment to Production
**As a** ops engineer
**I want** to deploy the application to production
**So that** real users can access it

**Acceptance Criteria:**
- [ ] Deployable to AWS/GCP
- [ ] Environment variables configured
- [ ] Database migrations run automatically
- [ ] Health checks configured
- [ ] Auto-scaling set up
- [ ] Monitoring enabled

**Tasks:**
- [ ] Create Dockerfile for backend
- [ ] Create Dockerfile for frontend
- [ ] Set up database backup strategy
- [ ] Configure environment variables
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Deploy to staging environment
- [ ] Test all features in staging
- [ ] Deploy to production
- [ ] Monitor for issues

**Test Cases:**
- [ ] Application starts successfully
- [ ] All endpoints work in production
- [ ] Database is backed up
- [ ] Logs are aggregated
- [ ] Monitoring is active

**Story Points:** 8

---

### STORY 6.6: Testing Coverage
**As a** developer
**I want** comprehensive test coverage
**So that** changes don't break existing functionality

**Acceptance Criteria:**
- [ ] Unit tests for all services (>80% coverage)
- [ ] Integration tests for API endpoints
- [ ] Frontend component tests
- [ ] E2E tests for critical workflows
- [ ] Tests run automatically on push

**Tasks:**
- [ ] Write unit tests for DataFetcher
- [ ] Write unit tests for AnalysisEngine
- [ ] Write unit tests for services
- [ ] Write integration tests for API endpoints
- [ ] Write component tests for frontend
- [ ] Write E2E tests for critical paths
- [ ] Set up coverage reporting
- [ ] Add tests to CI pipeline

**Test Cases:**
- [ ] All services have unit tests
- [ ] All endpoints have integration tests
- [ ] Critical user flows have E2E tests
- [ ] Coverage is >80%

**Story Points:** 8

---

## SUMMARY

**Total Stories:** 42
**Total Story Points:** ~210
**Estimated Timeline:** 12 weeks (2.5 weeks per phase, assuming 20 points/week velocity)

### Story Status Tracker
- [ ] Phase 1: Foundation (8 stories, ~36 points)
- [ ] Phase 2: API Endpoints (7 stories, ~31 points)
- [ ] Phase 3: Analysis Engine (4 stories, ~15 points)
- [ ] Phase 4: Frontend MVP (6 stories, ~22 points)
- [ ] Phase 5: Advanced Features (5 stories, ~26 points)
- [ ] Phase 6: Polish & Deployment (6 stories, ~32 points)

---

## How to Use This Document

1. **For Development:** Create a GitHub issue for each story
2. **For Tracking:** Use GitHub Projects to track progress
3. **For Estimation:** Story points help estimate effort
4. **For Testing:** Acceptance criteria are the definition of done
5. **For Review:** Tasks break work into reviewable chunks

Each story is independent and can be worked on in parallel (with dependencies noted).
