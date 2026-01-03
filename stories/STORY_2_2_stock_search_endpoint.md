# STORY 2.2: Stock Search & Discovery Endpoint

**Phase:** 2 (API Endpoints)
**Story Points:** 3
**Status:** Pending

---

## User Story

**As a** frontend developer
**I want** to search for stocks by ticker or name
**So that** users can find stocks to analyze

---

## Acceptance Criteria

- [ ] GET /stocks/search?q=AVANTI&market=NSE returns matching stocks
- [ ] Returns max 10 results by default
- [ ] Results include ticker, name, current price, analysis status
- [ ] Searches are case-insensitive
- [ ] Handles market filtering (NSE, BSE, NYSE)

---

## Implementation Tasks

- [ ] Create `stocks.py` router
- [ ] Implement `GET /stocks/search` endpoint
- [ ] Add database query for ticker/name fuzzy search
- [ ] Add market filtering
- [ ] Add pagination (limit, offset)
- [ ] Add tests for various search queries
- [ ] Document endpoint in docs/API.md

---

## Test Cases

- [ ] Search finds stock by exact ticker
- [ ] Search finds stock by partial name
- [ ] Search is case-insensitive
- [ ] Search respects market filter
- [ ] Search returns empty list for no matches
- [ ] Search handles special characters safely

---

## Dependencies

- STORY 2.1: Pydantic Schemas for Request/Response
- STORY 1.2: Database Schema & Migrations
- Fuzzy search library (fuzzywuzzy or similar)
- FastAPI routing

---

## Notes

- Implement fuzzy matching for better UX (handles typos)
- Add query parameter validation (market should be one of: NSE, BSE, NYSE)
- Consider database indexing on ticker and name for performance
- Response should include additional metadata like sector, 52-week high/low
- Cache search results in Redis for common queries (e.g., popular tickers)
- Implement rate limiting to prevent search abuse
- Return pagination info (total count, page, has_more) even for limited results
- Add search analytics to understand popular searches
