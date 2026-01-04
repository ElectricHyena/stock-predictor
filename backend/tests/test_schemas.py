"""Tests for Pydantic schemas"""

import pytest
from datetime import datetime, date, timedelta
from pydantic import ValidationError

from app.schemas import (
    # Base schemas
    Stock,
    StockPrice,
    NewsEvent,
    Prediction,
    BacktestMetric,
    InsightCategory,
    ErrorDetail,
    MarketEnum,
    AnalysisStatusEnum,
    EventCategoryEnum,
    SentimentCategoryEnum,
    PriceDirectionEnum,
    TimingEnum,
    # Request schemas
    StockSearchRequest,
    StockDetailRequest,
    PredictionRequest,
    HistoricalAnalysisRequest,
    BacktestRequest,
    BacktestStrategy,
    CreateAlertRequest,
    WatchlistRequest,
    # Response schemas
    StockSearchResult,
    StockSearchResponse,
    PriceHistoryPoint,
    StockDetailResponse,
    PredictabilityMetrics,
    PredictionResponse,
    PatternAnalysis,
    PatternOccurrence,
    HistoricalAnalysisResponse,
    BacktestResult,
    BacktestResponse,
    ErrorResponse,
    HealthResponse,
    SuccessResponse,
)


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestEnums:
    """Test enum definitions"""

    def test_market_enum_values(self):
        """Test market enum has correct values"""
        assert MarketEnum.NSE.value == "NSE"
        assert MarketEnum.BSE.value == "BSE"
        assert MarketEnum.NYSE.value == "NYSE"
        assert MarketEnum.NASDAQ.value == "NASDAQ"

    def test_analysis_status_enum_values(self):
        """Test analysis status enum"""
        assert AnalysisStatusEnum.PENDING.value == "PENDING"
        assert AnalysisStatusEnum.PROCESSING.value == "PROCESSING"
        assert AnalysisStatusEnum.COMPLETED.value == "COMPLETED"
        assert AnalysisStatusEnum.FAILED.value == "FAILED"

    def test_price_direction_enum(self):
        """Test price direction enum"""
        assert PriceDirectionEnum.UP.value == "UP"
        assert PriceDirectionEnum.DOWN.value == "DOWN"
        assert PriceDirectionEnum.SIDEWAYS.value == "SIDEWAYS"

    def test_timing_enum(self):
        """Test timing enum"""
        assert TimingEnum.SAME_DAY.value == "same-day"
        assert TimingEnum.NEXT_DAY.value == "next-day"


# ============================================================================
# BASE SCHEMA TESTS
# ============================================================================

class TestStockSchema:
    """Test Stock base schema"""

    def test_valid_stock(self):
        """Test creating valid stock"""
        stock = Stock(
            id=1,
            ticker="AAPL",
            company_name="Apple Inc.",
            market=MarketEnum.NYSE,
            sector="Technology",
            industry="Consumer Electronics",
            website="https://www.apple.com",
            description="Apple Inc. designs, manufactures...",
            analysis_status=AnalysisStatusEnum.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert stock.ticker == "AAPL"
        assert stock.market == MarketEnum.NYSE

    def test_stock_ticker_uppercase_conversion(self):
        """Test ticker is converted to uppercase"""
        stock = Stock(
            id=1,
            ticker="aapl",
            company_name="Apple",
            market=MarketEnum.NYSE,
            analysis_status=AnalysisStatusEnum.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert stock.ticker == "AAPL"

    def test_stock_missing_required_fields(self):
        """Test stock validation with missing required fields"""
        with pytest.raises(ValidationError) as exc_info:
            Stock(
                id=1,
                ticker="AAPL",
                market=MarketEnum.NYSE,
                created_at=datetime.now(),
                # Missing updated_at and analysis_status
            )
        errors = exc_info.value.errors()
        assert len(errors) >= 1

    def test_stock_optional_fields(self):
        """Test stock with minimal required fields"""
        stock = Stock(
            id=1,
            ticker="AAPL",
            market=MarketEnum.NYSE,
            analysis_status=AnalysisStatusEnum.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert stock.company_name is None
        assert stock.sector is None


class TestStockPriceSchema:
    """Test StockPrice base schema"""

    def test_valid_stock_price(self):
        """Test creating valid stock price"""
        price = StockPrice(
            id=1,
            stock_id=1,
            date=date.today(),
            open_price=150.0,
            high_price=155.0,
            low_price=148.0,
            close_price=152.0,
            volume=50000000,
            daily_return_pct=1.33,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert price.close_price == 152.0
        assert price.daily_return_pct == 1.33

    def test_stock_price_negative_price(self):
        """Test stock price validation rejects negative prices"""
        with pytest.raises(ValidationError) as exc_info:
            StockPrice(
                id=1,
                stock_id=1,
                date=date.today(),
                open_price=-10.0,  # Invalid
                close_price=150.0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        errors = exc_info.value.errors()
        assert any("greater than or equal to 0" in str(e) for e in errors)

    def test_stock_price_invalid_return_pct(self):
        """Test stock price validation rejects invalid return percentage"""
        with pytest.raises(ValidationError) as exc_info:
            StockPrice(
                id=1,
                stock_id=1,
                date=date.today(),
                close_price=150.0,
                daily_return_pct=150.0,  # Invalid: > 100
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        errors = exc_info.value.errors()
        # Check for validation error on daily_return_pct field
        assert any("daily_return_pct" in str(e) or "less than or equal to 100" in str(e) for e in errors)


class TestNewsEventSchema:
    """Test NewsEvent base schema"""

    def test_valid_news_event(self):
        """Test creating valid news event"""
        news = NewsEvent(
            id=1,
            stock_id=1,
            headline="Apple Announces Record Q4 Earnings",
            content="Apple Inc. reported its strongest quarter...",
            event_date=date.today(),
            event_category=EventCategoryEnum.EARNINGS,
            sentiment_score=0.85,
            sentiment_category=SentimentCategoryEnum.POSITIVE,
            source_name="Reuters",
            published_at=datetime.now(),
            fetched_at=datetime.now(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert news.sentiment_score == 0.85
        assert news.event_category == EventCategoryEnum.EARNINGS

    def test_news_event_invalid_sentiment_score(self):
        """Test news event sentiment validation"""
        with pytest.raises(ValidationError):
            NewsEvent(
                id=1,
                stock_id=1,
                headline="Test",
                event_date=date.today(),
                event_category=EventCategoryEnum.EARNINGS,
                sentiment_score=1.5,  # Invalid: > 1.0
                fetched_at=datetime.now(),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )


class TestPredictionSchema:
    """Test Prediction schema"""

    def test_valid_prediction(self):
        """Test creating valid prediction"""
        pred = Prediction(
            direction=PriceDirectionEnum.UP,
            confidence=0.78,
            expected_move_min=2.0,
            expected_move_max=4.0,
            expected_move_description="+2% to +4%",
            timing=TimingEnum.SAME_DAY,
            historical_win_rate=0.72,
            sample_size=45,
            reasoning="Pattern shows strong momentum",
        )
        assert pred.direction == PriceDirectionEnum.UP
        assert pred.confidence == 0.78

    def test_prediction_invalid_confidence(self):
        """Test prediction rejects invalid confidence"""
        with pytest.raises(ValidationError):
            Prediction(
                direction=PriceDirectionEnum.UP,
                confidence=1.5,  # Invalid
                expected_move_min=2.0,
                expected_move_max=4.0,
                expected_move_description="+2% to +4%",
                timing=TimingEnum.SAME_DAY,
                historical_win_rate=0.72,
                sample_size=45,
                reasoning="Test",
            )


# ============================================================================
# REQUEST SCHEMA TESTS
# ============================================================================

class TestStockSearchRequest:
    """Test StockSearchRequest schema"""

    def test_valid_search_request(self):
        """Test valid search request"""
        req = StockSearchRequest(
            query="Apple",
            market=MarketEnum.NYSE,
            limit=20,
            offset=0,
        )
        assert req.query == "Apple"
        assert req.limit == 20

    def test_search_request_empty_query(self):
        """Test search request rejects empty query"""
        with pytest.raises(ValidationError):
            StockSearchRequest(
                query="   ",  # Whitespace only
                limit=20,
            )

    def test_search_request_limit_validation(self):
        """Test search request limit validation"""
        with pytest.raises(ValidationError):
            StockSearchRequest(
                query="Apple",
                limit=1000,  # > 100
            )

    def test_search_request_offset_validation(self):
        """Test search request offset validation"""
        with pytest.raises(ValidationError):
            StockSearchRequest(
                query="Apple",
                offset=-1,  # Invalid
            )


class TestStockDetailRequest:
    """Test StockDetailRequest schema"""

    def test_valid_detail_request(self):
        """Test valid detail request"""
        req = StockDetailRequest(
            ticker="AAPL",
            include_prices=True,
            include_news=True,
            days_history=30,
        )
        assert req.ticker == "AAPL"

    def test_detail_request_ticker_uppercase(self):
        """Test ticker is uppercased"""
        req = StockDetailRequest(
            ticker="aapl",
            include_prices=True,
        )
        assert req.ticker == "AAPL"

    def test_detail_request_invalid_days(self):
        """Test invalid days_history"""
        with pytest.raises(ValidationError):
            StockDetailRequest(
                ticker="AAPL",
                days_history=400,  # > 365
            )


class TestPredictionRequest:
    """Test PredictionRequest schema"""

    def test_valid_prediction_request(self):
        """Test valid prediction request"""
        req = PredictionRequest(
            ticker="AAPL",
            timing=TimingEnum.SAME_DAY,
            confidence_threshold=0.6,
        )
        assert req.ticker == "AAPL"

    def test_prediction_request_confidence_range(self):
        """Test confidence threshold validation"""
        with pytest.raises(ValidationError):
            PredictionRequest(
                ticker="AAPL",
                confidence_threshold=1.5,  # > 1.0
            )


class TestHistoricalAnalysisRequest:
    """Test HistoricalAnalysisRequest schema"""

    def test_valid_analysis_request(self):
        """Test valid analysis request"""
        start = date(2023, 1, 1)
        end = date(2024, 1, 1)
        req = HistoricalAnalysisRequest(
            ticker="AAPL",
            start_date=start,
            end_date=end,
        )
        assert req.ticker == "AAPL"

    def test_analysis_request_invalid_date_range(self):
        """Test invalid date range"""
        with pytest.raises(ValidationError):
            HistoricalAnalysisRequest(
                ticker="AAPL",
                start_date=date(2024, 1, 1),
                end_date=date(2023, 1, 1),  # Before start
            )


class TestBacktestRequest:
    """Test BacktestRequest schema"""

    def test_valid_backtest_request(self):
        """Test valid backtest request"""
        strategy = BacktestStrategy(
            name="Earnings Momentum",
            entry_signal="earnings_beat",
            exit_signal="price_target_hit",
        )
        req = BacktestRequest(
            ticker="AAPL",
            start_date=date(2023, 1, 1),
            end_date=date(2024, 1, 1),
            initial_capital=100000.0,
            strategy=strategy,
        )
        assert req.ticker == "AAPL"
        assert req.strategy.name == "Earnings Momentum"

    def test_backtest_request_invalid_dates(self):
        """Test invalid backtest date range"""
        strategy = BacktestStrategy(
            name="Test",
            entry_signal="test",
            exit_signal="test",
        )
        with pytest.raises(ValidationError):
            BacktestRequest(
                ticker="AAPL",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 1),  # Equal to start
                initial_capital=100000.0,
                strategy=strategy,
            )


class TestCreateAlertRequest:
    """Test CreateAlertRequest schema"""

    def test_valid_alert_request(self):
        """Test valid alert request"""
        req = CreateAlertRequest(
            ticker="AAPL",
            alert_type="price_target",
            threshold_value=150.0,
            operator=">",
            is_active=True,
        )
        assert req.ticker == "AAPL"
        assert req.threshold_value == 150.0


class TestWatchlistRequest:
    """Test WatchlistRequest schema"""

    def test_valid_watchlist_request(self):
        """Test valid watchlist request"""
        req = WatchlistRequest(
            name="Tech Stocks",
            description="Top tech companies",
            tickers=["AAPL", "MSFT", "GOOG"],
        )
        assert len(req.tickers) == 3
        assert req.tickers[0] == "AAPL"

    def test_watchlist_request_ticker_uppercase(self):
        """Test tickers are uppercased"""
        req = WatchlistRequest(
            name="Tech Stocks",
            tickers=["aapl", "msft"],
        )
        assert req.tickers == ["AAPL", "MSFT"]

    def test_watchlist_request_empty_tickers(self):
        """Test watchlist rejects empty ticker list"""
        with pytest.raises(ValidationError):
            WatchlistRequest(
                name="Test",
                tickers=[],
            )


# ============================================================================
# RESPONSE SCHEMA TESTS
# ============================================================================

class TestStockSearchResponse:
    """Test StockSearchResponse schema"""

    def test_valid_search_response(self):
        """Test valid search response"""
        result = StockSearchResult(
            id=1,
            ticker="AAPL",
            company_name="Apple Inc.",
            market="NYSE",
            current_price=191.80,
            has_analysis=True,
            analysis_status="COMPLETED",
        )
        response = StockSearchResponse(
            total=1,
            limit=20,
            offset=0,
            results=[result],
        )
        assert response.total == 1
        assert len(response.results) == 1


class TestStockDetailResponse:
    """Test StockDetailResponse schema"""

    def test_valid_detail_response(self):
        """Test valid detail response"""
        response = StockDetailResponse(
            id=1,
            ticker="AAPL",
            company_name="Apple Inc.",
            market="NYSE",
            sector="Technology",
            analysis_status="COMPLETED",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert response.ticker == "AAPL"
        assert response.current_price is None  # Optional

    def test_detail_response_with_price_history(self):
        """Test detail response with price history"""
        history_point = PriceHistoryPoint(
            date=date.today(),
            close=191.80,
            open=190.50,
            high=192.75,
            low=189.25,
            volume=52000000,
        )
        response = StockDetailResponse(
            id=1,
            ticker="AAPL",
            market="NYSE",
            analysis_status="COMPLETED",
            current_price=191.80,
            price_history=[history_point],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert len(response.price_history) == 1
        assert response.price_history[0].close == 191.80


class TestPredictionResponse:
    """Test PredictionResponse schema"""

    def test_valid_prediction_response(self):
        """Test valid prediction response"""
        prediction = Prediction(
            direction=PriceDirectionEnum.UP,
            confidence=0.78,
            expected_move_min=2.0,
            expected_move_max=4.0,
            expected_move_description="+2% to +4%",
            timing=TimingEnum.SAME_DAY,
            historical_win_rate=0.72,
            sample_size=45,
            reasoning="Test reasoning",
        )
        metrics = PredictabilityMetrics(
            overall_score=72,
            information_availability=85,
            pattern_consistency=68,
            timing_certainty=65,
            direction_confidence=75,
            confidence=0.72,
        )
        response = PredictionResponse(
            ticker="AAPL",
            timestamp=datetime.now(),
            prediction=prediction,
            predictability=metrics,
            contributing_factors=[],
            disclaimer="This is a disclaimer",
        )
        assert response.ticker == "AAPL"
        assert response.prediction.direction == PriceDirectionEnum.UP


class TestHistoricalAnalysisResponse:
    """Test HistoricalAnalysisResponse schema"""

    def test_valid_analysis_response(self):
        """Test valid analysis response"""
        response = HistoricalAnalysisResponse(
            ticker="AAPL",
            analysis_period_start=date(2023, 1, 1),
            analysis_period_end=date(2024, 1, 1),
            total_trading_days=252,
            patterns_found=[],
            key_insights=[],
        )
        assert response.ticker == "AAPL"
        assert response.total_trading_days == 252


class TestBacktestResponse:
    """Test BacktestResponse schema"""

    def test_valid_backtest_response_success(self):
        """Test valid successful backtest response"""
        result = BacktestResult(
            ticker="AAPL",
            strategy_name="Earnings Momentum",
            backtest_period_start=date(2023, 1, 1),
            backtest_period_end=date(2024, 1, 1),
            initial_capital=100000.0,
            final_capital=124500.0,
            total_return_pct=24.5,
            num_trades=12,
            winning_trades=10,
            losing_trades=2,
            win_rate=0.833,
            avg_win_pct=2.8,
            avg_loss_pct=-1.5,
            max_drawdown_pct=5.2,
            trades=[],
            metrics=[],
        )
        response = BacktestResponse(
            status="success",
            result=result,
        )
        assert response.status == "success"
        assert response.result.total_return_pct == 24.5

    def test_valid_backtest_response_error(self):
        """Test valid error backtest response"""
        response = BacktestResponse(
            status="error",
            error="Insufficient data for backtest",
        )
        assert response.status == "error"
        assert response.result is None


class TestErrorResponse:
    """Test ErrorResponse schema"""

    def test_valid_error_response(self):
        """Test valid error response"""
        response = ErrorResponse(
            code="INVALID_TICKER",
            message="Stock ticker not found",
            timestamp=datetime.now(),
        )
        assert response.code == "INVALID_TICKER"
        assert response.status == "error"

    def test_error_response_with_details(self):
        """Test error response with details"""
        detail = ErrorDetail(
            field="ticker",
            message="Ticker does not exist",
            code="TICKER_NOT_FOUND",
        )
        response = ErrorResponse(
            code="VALIDATION_ERROR",
            message="Validation failed",
            details=[detail],
            timestamp=datetime.now(),
        )
        assert len(response.details) == 1


class TestHealthResponse:
    """Test HealthResponse schema"""

    def test_valid_health_response(self):
        """Test valid health response"""
        response = HealthResponse(
            status="healthy",
            service="stock-predictor-api",
            timestamp=datetime.now(),
            version="1.0.0",
        )
        assert response.status == "healthy"
        assert response.service == "stock-predictor-api"


class TestSuccessResponse:
    """Test SuccessResponse schema"""

    def test_valid_success_response(self):
        """Test valid success response"""
        response = SuccessResponse(
            message="Operation completed",
            timestamp=datetime.now(),
        )
        assert response.status == "success"
        assert response.message == "Operation completed"


# ============================================================================
# NESTED SCHEMA TESTS
# ============================================================================

class TestNestedSchemas:
    """Test nested schema compositions"""

    def test_stock_search_response_nested(self):
        """Test nested stock search result in response"""
        results = [
            StockSearchResult(
                id=1,
                ticker="AAPL",
                company_name="Apple",
                market="NYSE",
                has_analysis=True,
                analysis_status="COMPLETED",
            ),
            StockSearchResult(
                id=2,
                ticker="MSFT",
                company_name="Microsoft",
                market="NYSE",
                has_analysis=True,
                analysis_status="COMPLETED",
            ),
        ]
        response = StockSearchResponse(
            total=2,
            limit=20,
            offset=0,
            results=results,
        )
        assert len(response.results) == 2
        assert response.results[0].ticker == "AAPL"

    def test_backtest_with_trades(self):
        """Test backtest result with trades"""
        from app.schemas import BacktestTrade

        trade = BacktestTrade(
            entry_date=date(2024, 1, 1),
            exit_date=date(2024, 1, 3),
            entry_price=150.0,
            exit_price=155.0,
            quantity=100,
            return_pct=3.33,
            entry_signal="earnings_beat",
            exit_signal="stop_loss_hit",
        )
        result = BacktestResult(
            ticker="AAPL",
            strategy_name="Test",
            backtest_period_start=date(2023, 1, 1),
            backtest_period_end=date(2024, 1, 1),
            initial_capital=100000.0,
            final_capital=103300.0,
            total_return_pct=3.3,
            num_trades=1,
            winning_trades=1,
            losing_trades=0,
            win_rate=1.0,
            avg_win_pct=3.33,
            avg_loss_pct=0.0,
            max_drawdown_pct=0.0,
            trades=[trade],
            metrics=[],
        )
        assert len(result.trades) == 1
        assert result.trades[0].return_pct == 3.33


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestSchemaExamples:
    """Test that schema examples are valid"""

    def test_stock_example_is_valid(self):
        """Test Stock example from config is valid"""
        example_data = {
            "id": 1,
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "market": "NYSE",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "website": "https://www.apple.com",
            "description": "Apple Inc. designs, manufactures, and markets smartphones...",
            "analysis_status": "COMPLETED",
            "last_price_updated_at": "2024-01-03T10:30:00Z",
            "last_news_updated_at": "2024-01-03T09:15:00Z",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-03T10:30:00Z"
        }
        stock = Stock(**example_data)
        assert stock.ticker == "AAPL"

    def test_prediction_response_example_is_valid(self):
        """Test PredictionResponse example from config is valid"""
        # This validates that the schema can be instantiated with its documented example
        from datetime import datetime

        prediction_data = Prediction(
            direction=PriceDirectionEnum.UP,
            confidence=0.78,
            expected_move_min=2.0,
            expected_move_max=4.0,
            expected_move_description="+2% to +4%",
            timing=TimingEnum.SAME_DAY,
            historical_win_rate=0.72,
            sample_size=45,
            reasoning="Pattern shows strong momentum after positive earnings with high information availability",
            pattern_type="earnings_driven_momentum",
            supporting_events=["Q4 earnings beat", "Positive guidance"]
        )
        metrics_data = PredictabilityMetrics(
            overall_score=72,
            information_availability=85,
            pattern_consistency=68,
            timing_certainty=65,
            direction_confidence=75,
            confidence=0.72
        )
        response = PredictionResponse(
            ticker="AAPL",
            timestamp=datetime(2024, 1, 3, 10, 30, 0),
            prediction=prediction_data,
            predictability=metrics_data,
            contributing_factors=[],
            disclaimer="This prediction is for educational purposes only..."
        )
        assert response.prediction.direction == PriceDirectionEnum.UP


# ============================================================================
# JSON SERIALIZATION TESTS
# ============================================================================

class TestSchemaSerialization:
    """Test schema JSON serialization"""

    def test_stock_search_response_json_serializable(self):
        """Test search response is JSON serializable"""
        result = StockSearchResult(
            id=1,
            ticker="AAPL",
            company_name="Apple",
            market="NYSE",
            has_analysis=True,
            analysis_status="COMPLETED",
        )
        response = StockSearchResponse(
            total=1,
            limit=20,
            offset=0,
            results=[result],
        )
        json_data = response.model_dump_json()
        assert "AAPL" in json_data

    def test_error_response_json_serializable(self):
        """Test error response is JSON serializable"""
        response = ErrorResponse(
            code="INVALID_TICKER",
            message="Stock not found",
            timestamp=datetime.now(),
        )
        json_data = response.model_dump_json()
        assert "INVALID_TICKER" in json_data

    def test_schema_from_json_round_trip(self):
        """Test schema can be created from JSON and serialized back"""
        original = StockSearchResult(
            id=1,
            ticker="AAPL",
            company_name="Apple",
            market="NYSE",
            current_price=191.80,
            has_analysis=True,
            analysis_status="COMPLETED",
        )
        json_str = original.model_dump_json()
        reconstructed = StockSearchResult.model_validate_json(json_str)
        assert reconstructed.ticker == original.ticker
        assert reconstructed.current_price == original.current_price


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_very_long_company_name(self):
        """Test handling of long company names"""
        long_name = "A" * 255
        stock = Stock(
            id=1,
            ticker="TEST",
            company_name=long_name,
            market=MarketEnum.NYSE,
            analysis_status=AnalysisStatusEnum.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert len(stock.company_name) == 255

    def test_stock_price_with_zero_volume(self):
        """Test stock price with zero volume"""
        price = StockPrice(
            id=1,
            stock_id=1,
            date=date.today(),
            close_price=100.0,
            volume=0,  # Zero volume
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert price.volume == 0

    def test_prediction_zero_confidence(self):
        """Test prediction with zero confidence"""
        pred = Prediction(
            direction=PriceDirectionEnum.UP,
            confidence=0.0,  # Zero confidence
            expected_move_min=0.0,
            expected_move_max=1.0,
            expected_move_description="up to 1%",
            timing=TimingEnum.SAME_DAY,
            historical_win_rate=0.5,
            sample_size=1,
            reasoning="Very low confidence",
        )
        assert pred.confidence == 0.0

    def test_backtest_with_zero_trades(self):
        """Test backtest result with zero trades"""
        result = BacktestResult(
            ticker="AAPL",
            strategy_name="No signals",
            backtest_period_start=date(2023, 1, 1),
            backtest_period_end=date(2024, 1, 1),
            initial_capital=100000.0,
            final_capital=100000.0,
            total_return_pct=0.0,
            num_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            avg_win_pct=0.0,
            avg_loss_pct=0.0,
            max_drawdown_pct=0.0,
            trades=[],
            metrics=[],
        )
        assert result.num_trades == 0
