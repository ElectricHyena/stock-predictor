# STORY 2.4: Predictability Score Endpoint

**Phase:** 2 (API Endpoints)
**Story Points:** 3
**Status:** Pending

---

## User Story

**As a** frontend developer
**I want** to get the current predictability score for a stock
**So that** I can display it prominently on the UI

---

## Acceptance Criteria

- [ ] GET /stocks/{ticker}/predictability-score returns score
- [ ] Score is 0-100 integer
- [ ] Returns 4 sub-scores (info, pattern, timing, direction)
- [ ] Returns confidence level
- [ ] Returns trading recommendation (TRADE_THIS, MAYBE, AVOID)

---

## Implementation Tasks

- [ ] Implement `GET /stocks/{ticker}/predictability-score` endpoint
- [ ] Call analysis engine to compute score
- [ ] Cache score in Redis for 5 minutes
- [ ] Return score with breakdown
- [ ] Add tests

---

## Test Cases

- [ ] Endpoint returns score 0-100
- [ ] Endpoint returns 4 sub-scores
- [ ] Endpoint returns confidence 0-1
- [ ] Endpoint caches in Redis

---

## Dependencies

- STORY 2.1: Pydantic Schemas for Request/Response
- STORY 1.2: Database Schema & Migrations
- STORY 3.4: Predictability Scoring Algorithm
- STORY 3.3: Event-Price Correlation Analysis
- FastAPI routing
- Redis for caching
- Analysis engine service

---

## Notes

- Score calculation should use weighted factors:
  - 30% Information Availability (based on news/events count)
  - 25% Pattern Quality (based on event-price correlations)
  - 25% Timing Consistency (how consistent is the timing of moves)
  - 20% Direction Confidence (how reliable is direction prediction)
- Sub-scores should be 0-100 integers
- Confidence level: 0-1 float (1 = very confident, 0 = low confidence)
- Trading recommendations:
  - TRADE_THIS: score >= 75 AND confidence >= 0.7
  - MAYBE: score 50-75 OR (score >= 75 AND confidence < 0.7)
  - AVOID: score < 50
- Cache 5 minutes in Redis with key pattern: `predictability:{ticker}`
- Include timestamp of last update and when cache expires
- Return reason/explanation for the score (which factors contributed most)
- Include historical win rate if available
- Consider returning score breakdown visualization data (bar chart data)
