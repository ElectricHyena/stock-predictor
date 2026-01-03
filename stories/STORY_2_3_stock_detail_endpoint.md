# STORY 2.3: Stock Detail Endpoint

**Phase:** 2 (API Endpoints)
**Story Points:** 2
**Status:** Pending

---

## User Story

**As a** frontend developer
**I want** to get detailed info about a specific stock
**So that** I can display it on the stock detail page

---

## Acceptance Criteria

- [ ] GET /stocks/{ticker} returns stock details
- [ ] Creates stock in DB if not exists
- [ ] Triggers async price/news fetch
- [ ] Returns current price, last updated times
- [ ] Handles unknown tickers gracefully

---

## Implementation Tasks

- [ ] Implement `GET /stocks/{ticker}` endpoint
- [ ] Auto-create stock if not found
- [ ] Trigger async data fetch tasks
- [ ] Return stock details + metadata
- [ ] Add error handling for invalid tickers
- [ ] Write tests

---

## Test Cases

- [ ] Known stock returns correct data
- [ ] Unknown stock is created and fetch triggered
- [ ] Stock data is returned as expected schema

---

## Dependencies

- STORY 2.1: Pydantic Schemas for Request/Response
- STORY 1.2: Database Schema & Migrations
- STORY 1.3: Data Fetcher Service - Yahoo Finance Integration
- STORY 1.4: News Fetcher Service - NewsAPI Integration
- STORY 1.5: Celery Tasks for Background Data Fetching
- FastAPI routing
- Celery task queue

---

## Notes

- Ticker should be converted to uppercase for consistency
- If stock doesn't exist, create it with status="PENDING" and trigger async fetch
- Return stock details with timestamps: created_at, last_price_updated, last_news_updated
- Include 52-week high/low if available, otherwise null
- Include market information (NSE, BSE, NYSE)
- Validate ticker format (should match pattern for the specified market)
- Add caching layer for frequently accessed stocks (5-15 minute TTL)
- Include metadata indicating if data fetch is in progress
- Consider returning partial data while async fetch completes (stale data with warning)
