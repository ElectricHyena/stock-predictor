---
# Sentiment Analysis

**Story ID:** STORY_3_2
**Phase:** 3 (Analysis Engine)
**Story Points:** 2
**Status:** Not Started

## User Story
**As a** data scientist
**I want** to calculate sentiment score for each news article
**So that** I can correlate sentiment direction and intensity with price movements

## Acceptance Criteria
- [ ] Sentiment score is -1 to +1 scale (negative to positive)
- [ ] Positive sentiment words increase score towards +1
- [ ] Negative sentiment words decrease score towards -1
- [ ] Neutral articles score between -0.2 and +0.2
- [ ] Fast calculation (<50ms per article)
- [ ] Lexicon-based approach for initial implementation
- [ ] Scored at both headline and full text levels
- [ ] Handles edge cases (ALL CAPS, multiple punctuation, slang)

## Implementation Tasks
- [ ] Create `calculate_sentiment()` method in DataFetcher or AnalysisEngine
- [ ] Build positive word list (50-100 words):
  - [ ] "gain", "surge", "profit", "strong", "bullish", "positive", "growth", "win", "excellent", "beat"
- [ ] Build negative word list (50-100 words):
  - [ ] "loss", "drop", "decline", "weak", "bearish", "negative", "falling", "miss", "poor", "warning"
- [ ] Implement sentiment calculation:
  - [ ] Count positive and negative words
  - [ ] Calculate: (positive - negative) / (positive + negative) or similar formula
  - [ ] Normalize to -1 to +1 range
- [ ] Test on sample articles from NewsAPI
- [ ] Measure accuracy against known sentiment (manual validation)
- [ ] Document word lists and methodology
- [ ] Consider VADER or TextBlob for improved accuracy
- [ ] Write unit tests for sentiment calculation
- [ ] Add performance benchmarks

## Test Cases
- [ ] Positive words (e.g., "surge", "gain", "profit") score > 0.5
- [ ] Negative words (e.g., "drop", "loss", "decline") score < -0.5
- [ ] Neutral articles (no strong sentiment words) score -0.2 to +0.2
- [ ] Mixed sentiment (some positive + some negative) scores between -0.5 and +0.5
- [ ] Multiple occurrences of same word increase sentiment magnitude
- [ ] Calculation completes in <50ms
- [ ] Scoring is consistent across multiple calls
- [ ] Handles special cases: ALL CAPS, punctuation, numbers
- [ ] Emoji sentiment recognized (if applicable)
- [ ] Headlines and full text produce same overall direction

## Dependencies
- STORY_1_4 (News Fetcher Service)

## Notes
- Start with simple lexicon approach for MVP
- Can be enhanced with TextBlob (built-in sentiment analysis) or VADER (financial-specific)
- Consider negation handling: "not good" should be negative
- Weights: could weight sentiment words by importance
- Scale: normalize to [-1, +1] with 0 = neutral
- Consider domain-specific words (stock market terminology)
- Store sentiment alongside news events in database
- Validation: manually score 50-100 articles to test accuracy
- Performance target: <50ms for real-time processing during data fetching

---
