# STORY 4.2: API Client Service Layer

## Overview
**Title:** API Client Service Layer
**Phase:** 4 (Frontend MVP)
**Points:** 4
**Status:** Pending

---

## User Story

**As a** frontend developer
**I want** typed API client with React Query
**So that** data fetching is consistent and cached

---

## Acceptance Criteria

- [ ] Axios client configured with base URL
- [ ] React Query hooks for each endpoint
- [ ] Type-safe requests and responses
- [ ] Automatic retry and error handling
- [ ] Request interceptor adds auth token

---

## Implementation Tasks

- [ ] Create `services/api.ts` with axios client
- [ ] Create `services/stockService.ts` with stock endpoints
- [ ] Create `services/predictionService.ts`
- [ ] Create `services/backtestService.ts`
- [ ] Create custom React Query hooks
- [ ] Add error handling
- [ ] Add tests

---

## Test Cases

- [ ] API client makes requests to correct URL
- [ ] React Query caches responses
- [ ] Errors are handled gracefully
- [ ] Auth token is sent in headers

---

## Dependencies

- STORY 4.1: Frontend Project Setup & Layout
- STORY 2.1: Pydantic Schemas for Request/Response

---

## Technical Specifications

### Core Services

#### 1. API Client (`services/api.ts`)

```typescript
// Base axios instance with configuration
- Base URL from env variable
- Default headers (Content-Type: application/json)
- Request interceptor (add auth token)
- Response interceptor (handle errors)
- Retry logic (3 attempts, exponential backoff)
- Timeout (30 seconds)
```

#### 2. Stock Service (`services/stockService.ts`)

Endpoints:
- `searchStocks(query: string, market?: string)` - GET /stocks/search
- `getStockDetail(ticker: string)` - GET /stocks/{ticker}
- `getStock(ticker: string)` - GET /stocks/{ticker}

#### 3. Prediction Service (`services/predictionService.ts`)

Endpoints:
- `getPredictabilityScore(ticker: string)` - GET /stocks/{ticker}/predictability-score
- `getPrediction(ticker: string)` - GET /stocks/{ticker}/prediction
- `getHistoricalAnalysis(ticker: string)` - GET /stocks/{ticker}/historical-analysis

#### 4. Backtest Service (`services/backtestService.ts`)

Endpoints:
- `runBacktest(request: BacktestRequest)` - POST /backtest/run
- `getBacktestResults(id: string)` - GET /backtest/{id}

### React Query Hooks

```typescript
// Stock Hooks
- useStockSearch(query: string, market?: string)
- useStockDetail(ticker: string)

// Prediction Hooks
- usePredictabilityScore(ticker: string)
- usePrediction(ticker: string)
- useHistoricalAnalysis(ticker: string)

// Backtest Hooks
- useRunBacktest(request: BacktestRequest)
- useBacktestResults(id: string)

// Watchlist Hooks
- useWatchlist()
- useAddToWatchlist()
- useRemoveFromWatchlist()

// Alert Hooks
- useAlerts()
- useCreateAlert()
- useUpdateAlert()
```

### Type Definitions

```typescript
// Response Types
interface Stock {
  ticker: string;
  name: string;
  market: string;
  currentPrice: number;
  lastUpdated: string;
}

interface PredictabilityScore {
  score: number;  // 0-100
  infoScore: number;
  patternScore: number;
  timingScore: number;
  directionScore: number;
  confidence: number;  // 0-1
  recommendation: 'TRADE_THIS' | 'MAYBE' | 'AVOID';
}

interface Prediction {
  direction: 'UP' | 'DOWN';
  magnitude: string;  // "+2% to +4%"
  timing: string;  // "same-day", "next-day", "lagged"
  winRate: number;  // 0-1
}

interface BacktestResult {
  totalTrades: number;
  winRate: number;
  totalPL: number;
  sharpeRatio: number;
  trades: Trade[];
}

interface Trade {
  entryDate: string;
  exitDate: string;
  entryPrice: number;
  exitPrice: number;
  quantity: number;
  pnl: number;
  pnlPercent: number;
}
```

### Error Handling

All services should handle:
- Network errors (timeout, no internet)
- API errors (400, 401, 404, 500)
- Invalid responses (missing fields, wrong types)
- Graceful fallbacks

Error responses should include:
- HTTP status code
- Error message
- Error code (for client handling)
- Timestamp

### Authentication

- Bearer token passed in Authorization header
- Token refresh on 401 response
- Logout on 403 response

### Caching Strategy

React Query configuration:
- Default: 5 minute cache
- Stock search: 10 minutes
- Predictability score: 5 minutes
- Historical analysis: 1 hour
- Backtest results: No cache (real-time)

### Request/Response Interceptors

**Request Interceptor:**
1. Add Authorization header if token exists
2. Add X-Request-ID for tracing
3. Add User-Agent header

**Response Interceptor:**
1. Handle 401 (refresh token or redirect to login)
2. Handle 403 (show permission denied)
3. Handle 500+ (show error message, log to Sentry)
4. Parse error message from response

---

## File Structure

```
frontend/
├── services/
│   ├── api.ts                    # Base axios client
│   ├── stockService.ts           # Stock endpoints
│   ├── predictionService.ts      # Prediction endpoints
│   ├── backtestService.ts        # Backtest endpoints
│   ├── watchlistService.ts       # Watchlist endpoints
│   └── alertService.ts           # Alert endpoints
├── hooks/
│   ├── queries/
│   │   ├── useStock.ts
│   │   ├── usePrediction.ts
│   │   └── useBacktest.ts
│   ├── mutations/
│   │   ├── useRunBacktest.ts
│   │   ├── useAddToWatchlist.ts
│   │   └── useCreateAlert.ts
│   └── index.ts                  # Export all hooks
├── types/
│   ├── api.ts                    # API response types
│   ├── common.ts                 # Common types
│   └── index.ts
└── utils/
    └── errorHandling.ts          # Error parsing utilities
```

---

## Package Dependencies

```json
{
  "axios": "^1.6.0",
  "@tanstack/react-query": "^5.0.0",
  "axios-retry": "^3.7.0"
}
```

---

## Environment Variables

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
NEXT_PUBLIC_API_TIMEOUT=30000
```

---

## Error Codes

Standard error codes returned by API:
- `INVALID_REQUEST`: 400 - Invalid request parameters
- `UNAUTHORIZED`: 401 - Missing or invalid auth token
- `FORBIDDEN`: 403 - User doesn't have permission
- `NOT_FOUND`: 404 - Resource not found
- `RATE_LIMITED`: 429 - Too many requests
- `SERVER_ERROR`: 500 - Unexpected server error
- `SERVICE_UNAVAILABLE`: 503 - Service temporarily unavailable

---

## Acceptance Definition

Story is complete when:
1. Base API client is configured with axios
2. Request/response interceptors are implemented
3. All service files are created with typed methods
4. React Query hooks are created for queries
5. React Query hooks are created for mutations
6. Error handling is comprehensive
7. Auth token is automatically added
8. Caching strategy is implemented
9. Tests cover happy paths and error cases
10. Services are documented with JSDoc comments
