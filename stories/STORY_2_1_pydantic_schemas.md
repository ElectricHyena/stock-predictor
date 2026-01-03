# STORY 2.1: Pydantic Schemas for Request/Response

**Phase:** 2 (API Endpoints)
**Story Points:** 3
**Status:** Pending

---

## User Story

**As a** API developer
**I want** strongly-typed request/response schemas
**So that** the API is self-documenting and validated

---

## Acceptance Criteria

- [ ] All API models defined in schemas.py
- [ ] Schemas use Pydantic for validation
- [ ] Schemas include examples in docstrings
- [ ] Response models match frontend expectations

---

## Implementation Tasks

- [ ] Create StockBase, StockResponse schemas
- [ ] Create PriceData, NewsEventResponse schemas
- [ ] Create PredictabilityScoreResponse schema
- [ ] Create PredictionResponse schema
- [ ] Create BacktestRequest, BacktestResult schemas
- [ ] Create Alert, Watchlist schemas
- [ ] Add example() methods to schemas
- [ ] Document all schemas in docs/API_SCHEMAS.md

---

## Test Cases

- [ ] Schema validates correct data
- [ ] Schema rejects invalid data with helpful error
- [ ] Schema converts types correctly
- [ ] Schema.model_validate_json works

---

## Dependencies

- Pydantic v2.0+
- FastAPI with integrated Pydantic support
- Python 3.10+

---

## Notes

- Use Pydantic V2 BaseModel for all schemas
- Include proper type hints (str, int, float, datetime, Optional, List, etc.)
- Add Config classes for JSON schema customization
- Consider field validators for complex validations
- Ensure schemas are reusable and composable (e.g., StockBase used in StockResponse)
- Add Config.json_schema_extra for OpenAPI documentation
