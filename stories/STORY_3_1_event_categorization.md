---
# Event Categorization Engine

**Story ID:** STORY_3_1
**Phase:** 3 (Analysis Engine)
**Story Points:** 3
**Status:** Not Started

## User Story
**As a** data scientist
**I want** to categorize all news events into specific types
**So that** I can analyze patterns by event type and understand their predictive power

## Acceptance Criteria
- [ ] Events are categorized into: earnings, policy, seasonal, technical, sector
- [ ] Categorization is rule-based and deterministic (reproducible)
- [ ] High accuracy (>90%) on test set of 100+ articles
- [ ] Fast categorization (<100ms per article)
- [ ] Each event has single primary category and optional secondary categories
- [ ] Categorization rules are documented and maintainable
- [ ] Confidence score provided for each categorization
- [ ] Edge cases handled gracefully

## Implementation Tasks
- [ ] Create `categorize_event()` method in analysis_engine.py
- [ ] Define categorization rules based on keywords for each category:
  - [ ] Earnings: "earnings", "Q1/Q2/Q3/Q4", "EPS", "revenue", "profit", "guidance"
  - [ ] Policy: "regulatory", "policy", "government", "SEC", "RBI", "tax", "subsidy"
  - [ ] Seasonal: "year-end", "Q4", "holiday", "festival", "quarter-end"
  - [ ] Technical: "IPO", "split", "dividend", "buyback", "listing"
  - [ ] Sector: industry-specific news, competitors, commodity prices
- [ ] Implement keyword matching with case insensitivity
- [ ] Add confidence scoring based on keyword matches
- [ ] Create test set of 100+ articles with known categories
- [ ] Measure accuracy on test set
- [ ] Optimize for performance (target <100ms)
- [ ] Document rules in docs/CATEGORIZATION_RULES.md
- [ ] Write unit tests for each category
- [ ] Write edge case tests

## Test Cases
- [ ] Earnings news (earnings release, Q1 results) categorized as earnings
- [ ] Policy news (regulatory change, tax announcement) categorized as policy
- [ ] Holiday news (Diwali, year-end closure) categorized as seasonal
- [ ] Technical news (stock split, dividend) categorized as technical
- [ ] Sector news (competitor activity, commodity news) categorized as sector
- [ ] Mixed news (earnings + tax policy) returns primary + secondary categories
- [ ] Categorization is consistent across multiple calls
- [ ] Confidence score between 0-1 reflects matching strength
- [ ] Unknown news defaults to sector category
- [ ] Performance <100ms per article

## Dependencies
- STORY_1_4 (News Fetcher Service)

## Notes
- Categories are mutually exclusive for primary classification
- Use rule-based approach for deterministic results (not ML-based)
- Keywords should be specific enough to avoid false positives
- Support multiple keywords per category for flexibility
- Confidence = (matched keywords / total keywords) * 100
- Document all rules and keywords for transparency
- Future improvement: Add NLP-based categorization for better accuracy
- Test coverage should include real articles from NewsAPI

---
