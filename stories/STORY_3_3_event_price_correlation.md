# STORY 3.3: Event-Price Correlation Analysis

## Overview
**Title:** Event-Price Correlation Analysis
**Phase:** 3 (Analysis Engine)
**Points:** 5
**Status:** Pending

---

## User Story

**As a** data scientist
**I want** to correlate past events with price moves
**So that** I can build predictive patterns

---

## Acceptance Criteria

- [ ] Analyze historical correlation for each event type
- [ ] Calculate: occurrences, avg move, win rate, timing
- [ ] Store results in EventPriceCorrelation table
- [ ] Regenerate correlations weekly
- [ ] Results feed into predictability scoring

---

## Implementation Tasks

- [ ] Create `analyze_event_correlation()` method
- [ ] Query all events and corresponding price moves
- [ ] Calculate statistics per event category
- [ ] Store in database
- [ ] Add Celery task to recalculate weekly
- [ ] Add tests

---

## Test Cases

- [ ] Correlation analysis finds historical patterns
- [ ] Win rates are accurate (verified manually)
- [ ] Results stored in database

---

## Dependencies

- STORY 3.1: Event Categorization Engine
- STORY 3.2: Sentiment Analysis
- STORY 1.2: Database Schema & Migrations

---

## Technical Notes

This story involves analyzing historical correlations between news events and stock price movements. The analysis should:

1. **Query Historical Data:** Retrieve all historical events and their corresponding price moves
2. **Calculate Statistics:** For each event category, compute:
   - Number of occurrences
   - Average price move
   - Win rate (% of times price moved as expected)
   - Timing of moves (same-day, next-day, lagged)
3. **Store Results:** Persist analysis in EventPriceCorrelation table
4. **Schedule Regeneration:** Set up Celery task to recalculate weekly
5. **Feed into Scoring:** Results will be used by Story 3.4 (Predictability Scoring)

---

## Acceptance Definition

Story is complete when:
1. Historical correlations are calculated accurately
2. Results are stored in database
3. Weekly regeneration task is configured
4. Test coverage validates accuracy
