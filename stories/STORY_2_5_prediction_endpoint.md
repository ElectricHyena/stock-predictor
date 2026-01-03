---
# Prediction Endpoint

**Story ID:** STORY_2_5
**Phase:** 2 (API Endpoints)
**Story Points:** 2
**Status:** Not Started

## User Story
**As a** frontend developer
**I want** to get current prediction (direction, magnitude, timing) for a stock
**So that** I can show users what move is expected

## Acceptance Criteria
- [ ] GET /stocks/{ticker}/prediction endpoint returns direction and magnitude
- [ ] Direction is UP/DOWN format
- [ ] Magnitude is formatted as "+2% to +4%" range
- [ ] Timing is same-day/next-day/lagged
- [ ] Returns historical win rate for the prediction pattern
- [ ] Endpoint returns proper error handling for invalid tickers
- [ ] Response includes prediction confidence score

## Implementation Tasks
- [ ] Implement `GET /stocks/{ticker}/prediction` endpoint in FastAPI
- [ ] Create prediction service to calculate direction and magnitude
- [ ] Implement timing calculation based on historical patterns
- [ ] Add historical win rate calculation
- [ ] Format response user-friendly with clear direction indicators
- [ ] Add caching for prediction results (15 minutes TTL)
- [ ] Write unit tests for prediction logic
- [ ] Write integration tests for the endpoint
- [ ] Add error handling for missing/invalid tickers
- [ ] Document endpoint in API documentation

## Test Cases
- [ ] Endpoint returns valid direction (UP or DOWN)
- [ ] Endpoint returns magnitude range correctly formatted
- [ ] Endpoint returns timing (same-day/next-day/lagged)
- [ ] Endpoint returns historical win rate percentage
- [ ] Endpoint returns confidence score between 0-1
- [ ] Endpoint handles invalid ticker gracefully
- [ ] Endpoint returns cached result within TTL
- [ ] Response schema matches OpenAPI specification

## Dependencies
- STORY_2_1 (Pydantic Schemas)
- STORY_3_1 (Event Categorization Engine)

## Notes
- Use prediction service from analysis engine
- Ensure prediction data is current (updated daily via Celery tasks)
- Direction should be based on majority of signals
- Magnitude should be range estimate (min-max)
- Win rate derived from historical correlation data
- Cache results to reduce database load

---
