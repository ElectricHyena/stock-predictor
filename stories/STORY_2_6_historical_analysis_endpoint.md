---
# Historical Analysis Endpoint

**Story ID:** STORY_2_6
**Phase:** 2 (API Endpoints)
**Story Points:** 5
**Status:** Not Started

## User Story
**As a** frontend developer
**I want** to get 1-year historical analysis for a stock
**So that** users can see what was predictable in the past and learn from historical patterns

## Acceptance Criteria
- [ ] GET /stocks/{ticker}/historical-analysis returns 1-year historical data
- [ ] Returns price performance stats (total return, wins, losses, volatility)
- [ ] Returns predictability breakdown (percentage of predictable vs unpredictable events)
- [ ] Returns event-by-event analysis with dates and outcomes
- [ ] Returns key insights and patterns discovered
- [ ] Returns event categorization breakdown (earnings, policy, technical, sector, seasonal)
- [ ] Endpoint supports date range customization
- [ ] Response is paginated for large datasets

## Implementation Tasks
- [ ] Create `GET /stocks/{ticker}/historical-analysis` endpoint
- [ ] Build historical analysis service to gather and aggregate data
- [ ] Calculate price performance statistics (returns, volatility, Sharpe ratio)
- [ ] Analyze event-price correlations from database
- [ ] Classify events as predictable/unpredictable based on thresholds
- [ ] Generate insights and pattern summaries
- [ ] Implement event categorization breakdown
- [ ] Add pagination support for event lists
- [ ] Cache results (1 hour TTL) to reduce computation
- [ ] Write comprehensive unit tests
- [ ] Write integration tests for the endpoint
- [ ] Document all calculation methodologies

## Test Cases
- [ ] Endpoint returns data for correct date range (1 year by default)
- [ ] Endpoint calculates total return correctly
- [ ] Endpoint calculates win rate (correct predictions vs total)
- [ ] Endpoint returns predictability percentage
- [ ] Endpoint returns event breakdown by category
- [ ] Endpoint includes event-by-event details (date, type, sentiment, prediction, actual move)
- [ ] Endpoint generates meaningful insights
- [ ] Pagination works correctly with limit and offset
- [ ] Endpoint handles invalid ticker gracefully
- [ ] Response includes timing information for all events

## Dependencies
- STORY_1_2 (Database Schema)
- STORY_1_3 (Data Fetcher Service)
- STORY_2_1 (Pydantic Schemas)
- STORY_3_3 (Event-Price Correlation Analysis)

## Notes
- Historical analysis should cover minimum 1 year of data
- Predictability threshold: events with win rate >= 60% are "predictable"
- Include volatility calculations for risk assessment
- Event breakdown should include: earnings, policy, technical, sector, seasonal
- Insights should highlight strongest patterns and notable events
- Cache strategically as analysis is computationally intensive
- Support custom date ranges in future iterations

---
