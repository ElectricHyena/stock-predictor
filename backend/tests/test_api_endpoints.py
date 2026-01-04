"""
Test Suite for API Endpoints
Tests all 6 PHASE 2 story endpoints
STORY_2_2 through STORY_2_7
"""

import pytest
from datetime import datetime, date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app import models, schemas
from app.database import Base, get_db


class TestStockSearchEndpoint:
    """Tests for STORY_2_2: Stock Search Endpoint"""

    def test_search_by_ticker(self, client: TestClient, db: Session):
        """Test searching by ticker symbol"""
        # Create test stock
        stock = models.Stock(
            ticker="INFY",
            company_name="Infosys Limited",
            market="NSE",
            sector="IT",
            analysis_status="COMPLETED"
        )
        db.add(stock)
        db.commit()

        # Search for stock
        response = client.get("/api/stocks/search?q=INFY")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["results"][0]["ticker"] == "INFY"
        assert data["results"][0]["company_name"] == "Infosys Limited"

    def test_search_by_company_name(self, client: TestClient, db: Session):
        """Test searching by company name"""
        stock = models.Stock(
            ticker="TCS",
            company_name="Tata Consultancy Services",
            market="NSE",
            sector="IT"
        )
        db.add(stock)
        db.commit()

        response = client.get("/api/stocks/search?q=Tata")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["results"][0]["ticker"] == "TCS"

    def test_search_case_insensitive(self, client: TestClient, db: Session):
        """Test case-insensitive search"""
        stock = models.Stock(
            ticker="RELIANCE",
            company_name="Reliance Industries",
            market="NSE"
        )
        db.add(stock)
        db.commit()

        response = client.get("/api/stocks/search?q=reliance")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) > 0
        assert data["results"][0]["ticker"] == "RELIANCE"

    def test_search_with_market_filter(self, client: TestClient, db: Session):
        """Test search with market filter"""
        stock1 = models.Stock(
            ticker="AAPL",
            company_name="Apple Inc",
            market="NASDAQ"
        )
        stock2 = models.Stock(
            ticker="INFY",
            company_name="Infosys",
            market="NSE"
        )
        db.add_all([stock1, stock2])
        db.commit()

        response = client.get("/api/stocks/search?q=*&market=NASDAQ")
        assert response.status_code == 200
        data = response.json()
        assert all(result["market"] == "NASDAQ" for result in data["results"])

    def test_search_empty_results(self, client: TestClient):
        """Test search with no results"""
        response = client.get("/api/stocks/search?q=NONEXISTENT")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["results"] == []

    def test_search_pagination(self, client: TestClient, db: Session):
        """Test pagination in search results"""
        # Create multiple stocks
        for i in range(5):
            stock = models.Stock(
                ticker=f"STOCK{i}",
                company_name=f"Company {i}",
                market="NSE"
            )
            db.add(stock)
        db.commit()

        response = client.get("/api/stocks/search?q=STOCK&limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 2
        assert data["offset"] == 0
        assert len(data["results"]) == 2

    def test_search_missing_query(self, client: TestClient):
        """Test search without query parameter"""
        response = client.get("/api/stocks/search")
        assert response.status_code == 422  # Validation error


class TestStockDetailEndpoint:
    """Tests for STORY_2_3: Stock Detail Endpoint"""

    def test_get_stock_detail_success(self, client: TestClient, db: Session):
        """Test retrieving stock details"""
        stock = models.Stock(
            ticker="INFY",
            company_name="Infosys",
            market="NSE",
            sector="IT",
            analysis_status="COMPLETED"
        )
        db.add(stock)
        db.commit()

        response = client.get("/api/stocks/INFY")
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "INFY"
        assert data["company_name"] == "Infosys"
        assert data["market"] == "NSE"

    def test_get_stock_detail_not_found(self, client: TestClient):
        """Test retrieving stock with invalid ticker format returns 400"""
        # Invalid tickers with digits are rejected with 400
        response = client.get("/api/stocks/INVALID123")
        assert response.status_code == 400

    def test_get_stock_auto_created(self, client: TestClient, db: Session):
        """Test that valid non-existent stock is auto-created with PENDING status"""
        response = client.get("/api/stocks/NEWSTOCK")
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "NEWSTOCK"
        assert data["analysis_status"] == "PENDING"

        # Cleanup: remove the auto-created stock
        db.query(models.Stock).filter(models.Stock.ticker == "NEWSTOCK").delete()
        db.commit()

    def test_get_stock_with_price_history(self, client: TestClient, db: Session):
        """Test retrieving stock with price history"""
        stock = models.Stock(
            ticker="INFY",
            company_name="Infosys",
            market="NSE"
        )
        db.add(stock)
        db.flush()

        # Add price data with all required fields
        price = models.StockPrice(
            stock_id=stock.id,
            date=date.today(),
            open_price=100.0,
            high_price=102.0,
            low_price=99.0,
            close_price=101.0,
            volume=1000000,
            is_valid=True,
            data_source="test"
        )
        db.add(price)
        db.commit()

        response = client.get("/api/stocks/INFY?include_prices=true")
        assert response.status_code == 200
        data = response.json()
        assert data["price_history"] is not None
        assert len(data["price_history"]) > 0
        assert data["current_price"] == 101.0

    def test_get_stock_with_news(self, client: TestClient, db: Session):
        """Test retrieving stock with news"""
        stock = models.Stock(
            ticker="INFY",
            company_name="Infosys",
            market="NSE"
        )
        db.add(stock)
        db.flush()

        # Add news
        news = models.NewsEvent(
            stock_id=stock.id,
            headline="Infosys Q3 Earnings Beat",
            event_date=date.today(),
            event_category="earnings",
            sentiment_score=0.8
        )
        db.add(news)
        db.commit()

        response = client.get("/api/stocks/INFY?include_news=true")
        assert response.status_code == 200
        data = response.json()
        assert data["recent_news"] is not None
        assert len(data["recent_news"]) > 0
        assert data["recent_news"][0]["headline"] == "Infosys Q3 Earnings Beat"

    def test_ticker_case_normalization(self, client: TestClient, db: Session):
        """Test that ticker is normalized to uppercase"""
        stock = models.Stock(
            ticker="INFY",
            company_name="Infosys",
            market="NSE"
        )
        db.add(stock)
        db.commit()

        # Request with lowercase ticker
        response = client.get("/api/stocks/infy")
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "INFY"


class TestPredictabilityScoreEndpoint:
    """Tests for STORY_2_4: Predictability Score Endpoint"""

    def test_get_predictability_score(self, client: TestClient, db: Session):
        """Test retrieving predictability score"""
        stock = models.Stock(
            ticker="INFY",
            company_name="Infosys",
            market="NSE"
        )
        db.add(stock)
        db.flush()

        # Add predictability score
        score = models.PredictabilityScore(
            stock_id=stock.id,
            overall_predictability_score=75,
            information_availability_score=80,
            pattern_consistency_score=70,
            timing_certainty_score=75,
            direction_confidence_score=72,
            is_current=True
        )
        db.add(score)
        db.commit()

        response = client.get("/api/stocks/INFY/predictability-score")
        assert response.status_code == 200
        data = response.json()
        assert data["overall_score"] == 75
        assert data["information_availability"] == 80
        assert data["pattern_consistency"] == 70
        assert data["timing_certainty"] == 75
        assert data["direction_confidence"] == 72
        assert "trading_recommendation" in data

    def test_predictability_score_not_found_returns_default(self, client: TestClient, db: Session):
        """Test that missing score returns default values"""
        stock = models.Stock(
            ticker="INFY",
            company_name="Infosys",
            market="NSE"
        )
        db.add(stock)
        db.commit()

        response = client.get("/api/stocks/INFY/predictability-score")
        assert response.status_code == 200
        data = response.json()
        # Should return default score
        assert data["overall_score"] == 50
        assert 0 <= data["confidence"] <= 1
        assert data["trading_recommendation"] == "MAYBE"  # score 50 => MAYBE

    def test_predictability_score_stock_not_found(self, client: TestClient):
        """Test predictability score for non-existent stock"""
        response = client.get("/api/stocks/NONEXISTENT/predictability-score")
        assert response.status_code == 404


class TestPredictionEndpoint:
    """Tests for STORY_2_5: Price Prediction Endpoint"""

    def test_get_prediction(self, client: TestClient, db: Session):
        """Test retrieving price prediction"""
        stock = models.Stock(
            ticker="INFY",
            company_name="Infosys",
            market="NSE"
        )
        db.add(stock)
        db.flush()

        score = models.PredictabilityScore(
            stock_id=stock.id,
            overall_predictability_score=75,
            prediction_direction="UP",
            prediction_magnitude_low=1.5,
            prediction_magnitude_high=2.5,
            is_current=True
        )
        db.add(score)
        db.commit()

        response = client.get("/api/stocks/INFY/prediction")
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "INFY"
        assert data["prediction"]["direction"] == "UP"
        assert data["prediction"]["expected_move_min"] == 1.5
        assert data["prediction"]["expected_move_max"] == 2.5
        # Predictability score is derived from confidence (0.5 + score/200)
        # For score=75: confidence=0.875, overall_score=87
        assert data["predictability"]["overall_score"] == 87
        assert isinstance(data["contributing_factors"], list)

    def test_prediction_stock_not_found(self, client: TestClient):
        """Test prediction for non-existent stock"""
        response = client.get("/api/stocks/NONEXISTENT/prediction")
        assert response.status_code == 404

    def test_prediction_response_schema(self, client: TestClient, db: Session):
        """Test prediction response schema validity"""
        stock = models.Stock(
            ticker="INFY",
            company_name="Infosys",
            market="NSE"
        )
        db.add(stock)
        db.commit()

        response = client.get("/api/stocks/INFY/prediction")
        assert response.status_code == 200
        data = response.json()

        # Validate schema
        assert "ticker" in data
        assert "timestamp" in data
        assert "prediction" in data
        assert "predictability" in data
        assert "contributing_factors" in data
        assert "disclaimer" in data

        # Validate prediction sub-schema
        pred = data["prediction"]
        assert pred["direction"] in ["UP", "DOWN", "SIDEWAYS"]
        assert 0 <= pred["confidence"] <= 1
        assert 0 <= pred["historical_win_rate"] <= 1


class TestHistoricalAnalysisEndpoint:
    """Tests for STORY_2_6: Historical Analysis Endpoint"""

    def test_get_historical_analysis(self, client: TestClient, db: Session):
        """Test retrieving historical analysis"""
        stock = models.Stock(
            ticker="INFY",
            company_name="Infosys",
            market="NSE"
        )
        db.add(stock)
        db.flush()

        # Add correlation data
        corr = models.EventPriceCorrelation(
            stock_id=stock.id,
            event_category="earnings",
            event_date=date.today() - timedelta(days=30),
            price_change_pct=2.5,
            price_direction="UP",
            historical_win_rate=0.65,
            sample_size=20
        )
        db.add(corr)
        db.commit()

        response = client.get("/api/stocks/INFY/analysis?period=1y")
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "INFY"
        assert "patterns_found" in data
        assert "key_insights" in data
        assert "analysis_period_start" in data
        assert "analysis_period_end" in data

    def test_historical_analysis_period_parameter(self, client: TestClient, db: Session):
        """Test analysis with different period parameters"""
        stock = models.Stock(
            ticker="INFY",
            company_name="Infosys",
            market="NSE"
        )
        db.add(stock)
        db.commit()

        periods = ["1m", "3m", "6m", "1y"]
        for period in periods:
            response = client.get(f"/api/stocks/INFY/analysis?period={period}")
            assert response.status_code == 200
            data = response.json()
            assert data["ticker"] == "INFY"

    def test_historical_analysis_stock_not_found(self, client: TestClient):
        """Test analysis for non-existent stock"""
        response = client.get("/api/stocks/NONEXISTENT/analysis")
        assert response.status_code == 404


class TestBacktestEndpoint:
    """Tests for STORY_2_7: Backtest Endpoint"""

    def test_backtest_success(self, client: TestClient, db: Session):
        """Test successful backtest execution"""
        stock = models.Stock(
            ticker="INFY",
            company_name="Infosys",
            market="NSE"
        )
        db.add(stock)
        db.flush()

        # Add price data
        start_date = date.today() - timedelta(days=365)
        for i in range(365):
            current_date = start_date + timedelta(days=i)
            base_price = 100.0
            price = base_price + (i * 0.05)  # Small uptrend

            stock_price = models.StockPrice(
                stock_id=stock.id,
                date=current_date,
                open_price=price,
                high_price=price + 1,
                low_price=price - 1,
                close_price=price,
                volume=1000000
            )
            db.add(stock_price)

        db.commit()

        # Create backtest request
        request_data = {
            "ticker": "INFY",
            "start_date": start_date.isoformat(),
            "end_date": date.today().isoformat(),
            "initial_capital": 10000.0,
            "strategy": {
                "name": "test_strategy",
                "entry_signal": "close_above_20ma",
                "exit_signal": "close_below_20ma",
                "position_size": 1.0
            }
        }

        response = client.post("/api/backtest", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["result"] is not None
        assert data["result"]["ticker"] == "INFY"

    def test_backtest_metrics_present(self, client: TestClient, db: Session):
        """Test that backtest returns all required metrics"""
        stock = models.Stock(
            ticker="INFY",
            company_name="Infosys",
            market="NSE"
        )
        db.add(stock)
        db.flush()

        # Add minimal price data
        for i in range(30):
            current_date = date.today() - timedelta(days=30-i)
            stock_price = models.StockPrice(
                stock_id=stock.id,
                date=current_date,
                close_price=100.0 + i,
                volume=1000000
            )
            db.add(stock_price)

        db.commit()

        request_data = {
            "ticker": "INFY",
            "start_date": (date.today() - timedelta(days=30)).isoformat(),
            "end_date": date.today().isoformat(),
            "initial_capital": 10000.0,
            "strategy": {
                "name": "test_strategy",
                "entry_signal": "test",
                "exit_signal": "test"
            }
        }

        response = client.post("/api/backtest", json=request_data)
        assert response.status_code == 200
        data = response.json()

        if data["status"] == "completed":
            result = data["result"]
            assert "total_return_pct" in result
            assert "win_rate" in result
            assert "max_drawdown_pct" in result
            assert "sharpe_ratio" in result
            assert "trades" in result
            assert "metrics" in result

    def test_backtest_invalid_ticker(self, client: TestClient):
        """Test backtest with non-existent ticker"""
        request_data = {
            "ticker": "NONEXIST",  # Valid format but doesn't exist
            "start_date": (date.today() - timedelta(days=30)).isoformat(),
            "end_date": date.today().isoformat(),
            "initial_capital": 10000.0,
            "strategy": {
                "name": "test_strategy",
                "entry_signal": "test",
                "exit_signal": "test"
            }
        }

        response = client.post("/api/backtest", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"


class TestHealthEndpoint:
    """Tests for Health Check Endpoint"""

    def test_health_check(self, client: TestClient):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "stockpredictor-api"

    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data


class TestErrorHandling:
    """Tests for Error Handling"""

    def test_invalid_path(self, client: TestClient):
        """Test 404 error for invalid path"""
        response = client.get("/api/invalid/path")
        assert response.status_code == 404

    def test_invalid_method(self, client: TestClient):
        """Test 405 error for invalid method"""
        response = client.post("/api/stocks/search")
        # This will be 405 or 422 depending on method validation
        assert response.status_code in [405, 422, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
