# STORY 3.4: Predictability Scoring Algorithm

## Overview
**Title:** Predictability Scoring Algorithm
**Phase:** 3 (Analysis Engine)
**Points:** 5
**Status:** Pending

---

## User Story

**As a** data scientist
**I want** to score predictability of each event type
**So that** users know which patterns to trade

---

## Acceptance Criteria

- [ ] Score is 0-100 integer
- [ ] Weighted average of 4 factors (info, pattern, timing, direction)
- [ ] Weights: 30% info, 25% pattern, 25% timing, 20% direction
- [ ] Fast calculation (<200ms)

---

## Implementation Tasks

- [ ] Implement `calculate_predictability_score()` method
- [ ] Implement 4 scoring methods for each factor
- [ ] Aggregate with weights
- [ ] Cache results
- [ ] Add tests with known scores
- [ ] Document scoring logic in docs/SCORING.md

---

## Test Cases

- [ ] High info availability increases score
- [ ] High win rate increases score
- [ ] Immediate timing increases score
- [ ] Final score is weighted correctly
- [ ] Score is always 0-100

---

## Dependencies

- STORY 3.3: Event-Price Correlation Analysis
- STORY 2.4: Predictability Score Endpoint

---

## Scoring Formula

The predictability score is calculated as a weighted average of 4 factors:

```
Score = (Info_Score × 0.30) + (Pattern_Score × 0.25) + (Timing_Score × 0.25) + (Direction_Score × 0.20)
```

### Factor Definitions

1. **Info Score (30%):** Availability and quality of information
   - More news articles = higher score
   - Recent articles = higher score
   - Multiple sources = higher score
   - Range: 0-100

2. **Pattern Score (25%):** Historical pattern reliability
   - Win rate from EventPriceCorrelation
   - Consistency across different periods
   - Number of historical occurrences
   - Range: 0-100

3. **Timing Score (25%):** Predictability of timing
   - Same-day moves = higher score
   - Next-day moves = medium score
   - Lagged moves = lower score
   - Range: 0-100

4. **Direction Score (20%):** Clarity of price direction prediction
   - Strong consensus direction = higher score
   - Weak/mixed signals = lower score
   - Sentiment alignment = higher score
   - Range: 0-100

---

## Performance Requirements

- Calculation must complete in < 200ms
- Results should be cached for 5 minutes
- Cache invalidation on new correlation data

---

## Technical Notes

This story implements the core scoring algorithm that powers the predictability scores shown throughout the application. It combines multiple signals into a single 0-100 score that guides trading decisions.

---

## Acceptance Definition

Story is complete when:
1. Score calculation method is implemented
2. All 4 factor scoring methods are implemented
3. Weighted aggregation is correct
4. Results are cached in Redis
5. Calculation completes in <200ms
6. Test coverage validates known scores
7. Scoring logic is documented
