"""Pydantic Schemas for Request/Response Validation"""

from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional


# Stock Schemas
class StockBase(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    market: str


class StockCreate(StockBase):
    pass


class StockResponse(StockBase):
    id: int
    sector: Optional[str] = None
    last_price_updated_at: Optional[datetime] = None
    analysis_status: str

    class Config:
        from_attributes = True


# Price Schemas
class PriceData(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    daily_return_pct: Optional[float] = None

    class Config:
        from_attributes = True


# News Schemas
class NewsEventResponse(BaseModel):
    id: int
    headline: str
    event_category: str
    sentiment_score: Optional[float] = None
    source_name: str
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Predictability Schemas
class PredictabilityScoreResponse(BaseModel):
    overall_score: int
    information_availability: int
    pattern_consistency: int
    timing_certainty: int
    direction_confidence: int
    confidence: float


class PredictionResponse(BaseModel):
    direction: str  # UP, DOWN
    expected_move: str  # "+2% to +4%"
    timing: str  # "same-day"
    historical_win_rate: float
    reasoning: str
    sample_size: int


# Search Schemas
class StockSearchResult(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    market: str
    current_price: Optional[float] = None
    has_analysis: bool


# Health Check
class HealthResponse(BaseModel):
    status: str
    service: str
