"""Comprehensive Pydantic Schemas for Request/Response Validation"""

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from datetime import datetime, date
from typing import List, Optional
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class MarketEnum(str, Enum):
    """Stock market type"""
    NSE = "NSE"
    BSE = "BSE"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"


class AnalysisStatusEnum(str, Enum):
    """Stock analysis status"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EventCategoryEnum(str, Enum):
    """News event category"""
    EARNINGS = "earnings"
    POLICY = "policy"
    SEASONAL = "seasonal"
    TECHNICAL = "technical"
    SECTOR = "sector"
    MERGER = "merger"
    DIVIDEND = "dividend"
    MANAGEMENT = "management"


class SentimentCategoryEnum(str, Enum):
    """Sentiment classification"""
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


class PriceDirectionEnum(str, Enum):
    """Price movement direction"""
    UP = "UP"
    DOWN = "DOWN"
    SIDEWAYS = "SIDEWAYS"


class TimingEnum(str, Enum):
    """Prediction timing"""
    SAME_DAY = "same-day"
    NEXT_DAY = "next-day"
    LAGGED = "lagged"
    INTRADAY = "intraday"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class TradingRecommendationEnum(str, Enum):
    """Trading recommendation based on predictability"""
    TRADE_THIS = "TRADE_THIS"
    MAYBE = "MAYBE"
    AVOID = "AVOID"


# ============================================================================
# BASE SCHEMAS
# ============================================================================

class Stock(BaseModel):
    """Base stock information"""
    id: int
    ticker: str
    company_name: Optional[str] = None
    market: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    analysis_status: str
    last_price_updated_at: Optional[datetime] = None
    last_news_updated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator('ticker')
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        """Ensure ticker is uppercase"""
        return v.upper() if v else v


class StockPrice(BaseModel):
    """OHLCV stock price data point"""
    id: int
    stock_id: int
    date: date
    open_price: Optional[float] = Field(None, ge=0, description="Opening price, must be >= 0")
    high_price: Optional[float] = Field(None, ge=0, description="High price, must be >= 0")
    low_price: Optional[float] = Field(None, ge=0, description="Low price, must be >= 0")
    close_price: Optional[float] = Field(None, ge=0, description="Closing price, must be >= 0")
    volume: Optional[int] = Field(None, ge=0, description="Trading volume, must be >= 0")
    adjusted_close: Optional[float] = Field(None, ge=0, description="Adjusted close, must be >= 0")
    daily_return_pct: Optional[float] = Field(None, ge=-100, le=100, description="Daily return between -100 and 100")
    price_range: Optional[float] = Field(None, ge=0, description="Price range, must be >= 0")
    is_valid: bool = True
    data_source: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NewsEvent(BaseModel):
    """News article or event related to a stock"""
    id: int
    stock_id: int
    headline: str
    content: Optional[str] = None
    event_date: date
    event_category: str
    event_subcategory: Optional[str] = None
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Sentiment score between -1 and 1")
    sentiment_category: Optional[str] = None
    source_name: Optional[str] = None
    source_quality: Optional[float] = Field(None, ge=0.0, le=1.0, description="Source quality between 0 and 1")
    original_url: Optional[str] = None
    published_at: Optional[datetime] = None
    fetched_at: datetime
    content_hash: Optional[str] = None
    is_duplicate: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Prediction(BaseModel):
    """Price movement prediction"""
    direction: str
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence between 0 and 1")
    expected_move_min: float
    expected_move_max: float
    expected_move_description: str
    timing: str
    historical_win_rate: float = Field(..., ge=0.0, le=1.0, description="Historical win rate between 0 and 1")
    sample_size: int = Field(..., ge=0, description="Sample size must be >= 0")
    reasoning: str
    pattern_type: Optional[str] = None
    supporting_events: Optional[List[str]] = None


class BacktestMetric(BaseModel):
    """Individual metric from backtest results"""
    name: str
    value: float
    unit: Optional[str] = None
    description: Optional[str] = None


class InsightCategory(BaseModel):
    """Insight derived from analysis"""
    category: str
    confidence: float
    description: str
    supporting_data: Optional[dict] = None


class ErrorDetail(BaseModel):
    """Error detail for error responses"""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class StockSearchRequest(BaseModel):
    """Request to search for stocks"""
    query: str
    market: Optional[str] = None
    sector: Optional[str] = None
    limit: int = Field(20, ge=1, le=100, description="Max results, between 1 and 100")
    offset: int = Field(0, ge=0, description="Offset must be >= 0")

    @field_validator('query')
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        """Ensure query has meaningful content"""
        if not v or not v.strip():
            raise ValueError('Search query cannot be empty')
        return v.strip()


class StockDetailRequest(BaseModel):
    """Request to get detailed stock information"""
    ticker: str
    include_prices: bool = True
    include_news: bool = True
    include_predictions: bool = False
    days_history: int = Field(30, ge=1, le=365, description="Days of history, between 1 and 365")

    @field_validator('ticker')
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        """Ensure ticker is uppercase"""
        return v.upper() if v else v


class PredictionRequest(BaseModel):
    """Request for price prediction on a stock"""
    ticker: str
    timing: Optional[str] = "same-day"
    include_reasoning: bool = True
    confidence_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Confidence threshold between 0 and 1")
    news_weight: float = Field(0.4, ge=0.0, le=1.0, description="News weight between 0 and 1")

    @field_validator('ticker')
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        """Ensure ticker is uppercase"""
        return v.upper() if v else v


class HistoricalAnalysisRequest(BaseModel):
    """Request for historical pattern analysis"""
    ticker: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    pattern_types: Optional[List[str]] = None
    min_occurrences: int = Field(3, ge=1, description="Minimum occurrences must be >= 1")
    include_metrics: bool = True

    @field_validator('ticker')
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        """Ensure ticker is uppercase"""
        return v.upper() if v else v

    @model_validator(mode='after')
    def validate_date_range(self):
        """Ensure end_date is after start_date if both provided"""
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError('end_date must be after start_date')
        return self


class BacktestStrategy(BaseModel):
    """Strategy configuration for backtesting"""
    name: str
    description: Optional[str] = None
    entry_signal: str
    exit_signal: str
    position_size: float = 1.0
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    max_holding_days: Optional[int] = None


class BacktestRequest(BaseModel):
    """Request to backtest a trading strategy"""
    ticker: str
    start_date: date
    end_date: date
    initial_capital: float = Field(10000.0, gt=0, description="Initial capital must be > 0")
    strategy: BacktestStrategy
    use_leverage: bool = False
    max_leverage: float = Field(1.0, ge=1.0, le=10.0, description="Max leverage between 1 and 10")
    include_slippage: bool = True
    slippage_pct: float = Field(0.1, ge=0.0, le=5.0, description="Slippage percentage between 0 and 5")

    @field_validator('ticker')
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        """Ensure ticker is uppercase"""
        return v.upper() if v else v

    @model_validator(mode='after')
    def validate_date_range(self):
        """Ensure end_date is after start_date"""
        if self.end_date <= self.start_date:
            raise ValueError('end_date must be after start_date')
        return self


class CreateAlertRequest(BaseModel):
    """Request to create a price alert"""
    ticker: str
    alert_type: str
    threshold_value: float
    operator: str
    is_active: bool = True
    notify_methods: Optional[List[str]] = None

    @field_validator('ticker')
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        """Ensure ticker is uppercase"""
        return v.upper() if v else v


class WatchlistRequest(BaseModel):
    """Request to manage watchlist"""
    name: str = Field(..., min_length=1, description="Watchlist name")
    description: Optional[str] = None
    tickers: List[str] = Field(..., min_length=1, description="At least one ticker required")

    @field_validator('tickers')
    @classmethod
    def validate_tickers(cls, v: List[str]) -> List[str]:
        """Ensure tickers are uppercase and not empty"""
        result = [ticker.upper() for ticker in v if ticker and ticker.strip()]
        if not result:
            raise ValueError('At least one valid ticker is required')
        return result


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class StockSearchResult(BaseModel):
    """Single result from stock search"""
    id: int
    ticker: str
    company_name: Optional[str] = None
    market: str
    sector: Optional[str] = None
    current_price: Optional[float] = None
    has_analysis: bool
    analysis_status: str

    model_config = ConfigDict(from_attributes=True)


class StockSearchResponse(BaseModel):
    """Response for stock search endpoint"""
    total: int
    limit: int
    offset: int
    results: List[StockSearchResult]


class PriceHistoryPoint(BaseModel):
    """Single point in price history"""
    date: date
    close: float
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[int] = None
    daily_return_pct: Optional[float] = None


class StockDetailResponse(BaseModel):
    """Comprehensive stock detail response"""
    id: int
    ticker: str
    company_name: Optional[str] = None
    market: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    analysis_status: str
    last_price_updated_at: Optional[datetime] = None
    last_news_updated_at: Optional[datetime] = None
    current_price: Optional[float] = None
    price_history: Optional[List[PriceHistoryPoint]] = None
    recent_news: Optional[List[NewsEvent]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PredictabilityMetrics(BaseModel):
    """Metrics indicating how predictable a stock is"""
    overall_score: int
    information_availability: int
    pattern_consistency: int
    timing_certainty: int
    direction_confidence: int
    confidence: float
    trading_recommendation: Optional[str] = None  # TRADE_THIS, MAYBE, AVOID


class PredictionResponse(BaseModel):
    """Response for price prediction request"""
    ticker: str
    timestamp: datetime
    prediction: Prediction
    predictability: PredictabilityMetrics
    contributing_factors: List[InsightCategory]
    disclaimer: str


class PatternOccurrence(BaseModel):
    """Single occurrence of a pattern"""
    date: date
    outcome: str
    return_pct: float
    holding_days: int


class PatternAnalysis(BaseModel):
    """Analysis of a recurring pattern"""
    pattern_name: str
    pattern_type: str
    occurrences: int
    win_rate: float
    avg_return: float
    min_return: float
    max_return: float
    avg_holding_days: int
    occurrences_detail: List[PatternOccurrence]


class HistoricalAnalysisResponse(BaseModel):
    """Response for historical pattern analysis"""
    ticker: str
    analysis_period_start: date
    analysis_period_end: date
    total_trading_days: int
    patterns_found: List[PatternAnalysis]
    key_insights: List[InsightCategory]


class BacktestTrade(BaseModel):
    """Single trade from backtest"""
    entry_date: date
    exit_date: Optional[date] = None
    entry_price: float
    exit_price: Optional[float] = None
    quantity: int
    return_pct: Optional[float] = None
    entry_signal: str
    exit_signal: Optional[str] = None


class BacktestResult(BaseModel):
    """Complete backtest results"""
    ticker: str
    strategy_name: str
    backtest_period_start: date
    backtest_period_end: date
    initial_capital: float
    final_capital: float
    total_return_pct: float
    num_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win_pct: float
    avg_loss_pct: float
    max_drawdown_pct: float
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    profit_factor: Optional[float] = None
    trades: List[BacktestTrade]
    metrics: List[BacktestMetric]


class BacktestResponse(BaseModel):
    """Response wrapper for backtest results"""
    status: str
    result: Optional[BacktestResult] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response"""
    status: str = "error"
    code: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime
    path: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    timestamp: datetime
    version: Optional[str] = None
    dependencies: Optional[dict] = None


class SuccessResponse(BaseModel):
    """Generic success response"""
    status: str = "success"
    message: str
    data: Optional[dict] = None
    timestamp: datetime


# ============================================================================
# LEGACY SCHEMAS (For backwards compatibility)
# ============================================================================

class StockBase(BaseModel):
    """Legacy stock base model"""
    ticker: str
    company_name: Optional[str] = None
    market: str


class StockCreate(StockBase):
    """Legacy stock create model"""
    pass


class StockResponse(StockBase):
    """Legacy stock response model"""
    id: int
    sector: Optional[str] = None
    last_price_updated_at: Optional[datetime] = None
    analysis_status: str

    class Config:
        from_attributes = True


class PriceData(BaseModel):
    """Legacy price data model"""
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    daily_return_pct: Optional[float] = None

    class Config:
        from_attributes = True


class NewsEventResponse(BaseModel):
    """Legacy news event response model"""
    id: int
    headline: str
    event_category: str
    sentiment_score: Optional[float] = None
    source_name: str
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PredictabilityScoreResponse(BaseModel):
    """Legacy predictability score model"""
    overall_score: int
    information_availability: int
    pattern_consistency: int
    timing_certainty: int
    direction_confidence: int
    confidence: float


class PredictionResponseLegacy(BaseModel):
    """Legacy prediction response model"""
    direction: str
    expected_move: str
    timing: str
    historical_win_rate: float
    reasoning: str
    sample_size: int


class StockSearchResultLegacy(BaseModel):
    """Legacy stock search result"""
    ticker: str
    company_name: Optional[str] = None
    market: str
    current_price: Optional[float] = None
    has_analysis: bool


# ============================================================================
# WATCHLIST SCHEMAS
# ============================================================================

class WatchlistItemResponse(BaseModel):
    """Watchlist item with stock details"""
    id: int
    stock_id: int
    ticker: str
    company_name: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = []
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WatchlistResponse(BaseModel):
    """Watchlist with items"""
    id: int
    name: str
    description: Optional[str] = None
    is_default: bool = False
    item_count: int
    items: List[WatchlistItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WatchlistCreateRequest(BaseModel):
    """Request to create a watchlist"""
    user_id: int
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Watchlist name cannot be empty')
        return v.strip()


class WatchlistUpdateRequest(BaseModel):
    """Request to update a watchlist"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class WatchlistAddStockRequest(BaseModel):
    """Request to add a stock to watchlist"""
    ticker: str
    market: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None

    @field_validator('ticker')
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        return v.upper() if v else v


class WatchlistUpdateItemRequest(BaseModel):
    """Request to update watchlist item"""
    notes: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None


# ============================================================================
# ALERT SCHEMAS
# ============================================================================

class AlertTypeEnum(str, Enum):
    """Alert type classification"""
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PRICE_CHANGE_PCT = "price_change_pct"
    PREDICTION_CHANGE = "prediction_change"
    VOLUME_SPIKE = "volume_spike"
    DIVIDEND = "dividend"
    PREDICTABILITY_CHANGE = "predictability_change"


class AlertFrequencyEnum(str, Enum):
    """Alert frequency"""
    REALTIME = "realtime"
    DAILY = "daily"
    WEEKLY = "weekly"


class AlertStatusEnum(str, Enum):
    """Alert status"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    DISABLED = "disabled"
    EXPIRED = "expired"


class AlertResponse(BaseModel):
    """Alert details response"""
    id: int
    user_id: int
    stock_id: int
    ticker: str
    alert_type: str
    condition_value: float
    condition_operator: str
    frequency: str
    status: str
    is_enabled: bool
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_count: int = 0
    last_triggered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertCreateRequest(BaseModel):
    """Request to create an alert"""
    user_id: int
    ticker: str
    alert_type: str
    condition_value: float
    condition_operator: Optional[str] = ">="
    frequency: Optional[str] = "realtime"
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    expires_at: Optional[datetime] = None

    @field_validator('ticker')
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        return v.upper() if v else v


class AlertUpdateRequest(BaseModel):
    """Request to update an alert"""
    condition_value: Optional[float] = None
    condition_operator: Optional[str] = None
    frequency: Optional[str] = None
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_enabled: Optional[bool] = None


class BulkAlertCreateRequest(BaseModel):
    """Request to create alerts for multiple stocks"""
    user_id: int
    tickers: List[str]
    alert_type: str
    condition_value: float
    condition_operator: Optional[str] = ">="
    frequency: Optional[str] = "realtime"

    @field_validator('tickers')
    @classmethod
    def validate_tickers(cls, v: List[str]) -> List[str]:
        return [ticker.upper() for ticker in v if ticker and ticker.strip()]


class AlertTriggerResponse(BaseModel):
    """Alert trigger history"""
    id: int
    alert_id: int
    triggered_value: float
    message: Optional[str] = None
    is_read: bool = False
    is_dismissed: bool = False
    triggered_at: datetime
    read_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
