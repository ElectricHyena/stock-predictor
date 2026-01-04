"""
Unit Tests for Yahoo Finance Data Fetcher Service
Tests cover fetching, validation, storage, and error handling
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.data_fetchers import YahooFinanceFetcher
from app.models.stock import Stock
from app.models.price import StockPrice
from app.exceptions import (
    InvalidTickerError,
    APIError,
    DataValidationError,
    DatabaseError,
)


# Test fixtures
@pytest.fixture
def mock_session():
    """Create a mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def fetcher(mock_session):
    """Create a YahooFinanceFetcher instance with mock session"""
    return YahooFinanceFetcher(mock_session)


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data"""
    dates = pd.date_range(start="2023-01-01", periods=10, freq="D")
    data = {
        "Open": [100.0, 101.0, 102.0, 101.5, 103.0, 102.5, 104.0, 105.0, 104.5, 106.0],
        "High": [102.0, 103.0, 104.0, 103.5, 105.0, 104.5, 106.0, 107.0, 106.5, 108.0],
        "Low": [99.0, 100.0, 101.0, 100.5, 102.0, 101.5, 103.0, 104.0, 103.5, 105.0],
        "Close": [101.5, 102.5, 103.5, 102.5, 104.5, 103.5, 105.5, 106.5, 105.5, 107.5],
        "Volume": [1000000, 1100000, 1200000, 950000, 1150000, 1050000, 1250000, 1350000, 1200000, 1400000],
        "Adj Close": [101.5, 102.5, 103.5, 102.5, 104.5, 103.5, 105.5, 106.5, 105.5, 107.5],
    }
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def sample_stock(mock_session):
    """Create a sample stock object"""
    stock = Mock(spec=Stock)
    stock.id = 1
    stock.ticker = "AAPL"
    return stock


# Tests for fetch_ohlcv
class TestFetchOHLCV:
    """Test single stock OHLCV fetching"""

    @patch("app.services.data_fetchers.yf.Ticker")
    def test_fetch_valid_ticker(self, mock_ticker_class, fetcher, sample_ohlcv_data):
        """Test successful fetch for valid ticker"""
        mock_ticker = Mock()
        mock_ticker.history.return_value = sample_ohlcv_data
        mock_ticker_class.return_value = mock_ticker

        result = fetcher.fetch_ohlcv("AAPL", datetime(2023, 1, 1), datetime(2023, 1, 10))

        assert not result.empty
        assert len(result) == 10
        assert "Open" in result.columns
        assert "Close" in result.columns
        assert "Volume" in result.columns
        mock_ticker.history.assert_called_once()

    @patch("app.services.data_fetchers.yf.Ticker")
    def test_fetch_empty_result(self, mock_ticker_class, fetcher):
        """Test handling of empty data (invalid ticker)"""
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_class.return_value = mock_ticker

        with pytest.raises((InvalidTickerError, APIError)):
            fetcher.fetch_ohlcv("INVALID123")

    @patch("app.services.data_fetchers.yf.Ticker")
    def test_fetch_invalid_ticker_format(self, mock_ticker_class, fetcher):
        """Test validation of ticker format"""
        with pytest.raises(InvalidTickerError):
            fetcher.fetch_ohlcv("")

        with pytest.raises(InvalidTickerError):
            fetcher.fetch_ohlcv("A" * 11)  # Too long

    @patch("app.services.data_fetchers.yf.Ticker")
    def test_fetch_with_default_dates(self, mock_ticker_class, fetcher, sample_ohlcv_data):
        """Test fetch with default date range (1 year back)"""
        mock_ticker = Mock()
        mock_ticker.history.return_value = sample_ohlcv_data
        mock_ticker_class.return_value = mock_ticker

        result = fetcher.fetch_ohlcv("AAPL")

        assert not result.empty
        # Verify history was called with reasonable date range
        call_args = mock_ticker.history.call_args
        assert "start" in call_args.kwargs or len(call_args.args) >= 1

    @patch("app.services.data_fetchers.yf.Ticker")
    def test_fetch_ticker_case_insensitivity(self, mock_ticker_class, fetcher, sample_ohlcv_data):
        """Test that ticker is converted to uppercase"""
        mock_ticker = Mock()
        mock_ticker.history.return_value = sample_ohlcv_data
        mock_ticker_class.return_value = mock_ticker

        result = fetcher.fetch_ohlcv("aapl")
        assert not result.empty

        # Verify the ticker was converted to uppercase
        mock_ticker_class.assert_called_with("AAPL")

    @patch("app.services.data_fetchers.yf.Ticker")
    def test_fetch_missing_columns(self, mock_ticker_class, fetcher):
        """Test handling of missing OHLCV columns"""
        mock_ticker = Mock()
        incomplete_data = pd.DataFrame({
            "Open": [100.0],
            "High": [102.0],
            "Close": [101.0]
            # Missing Low and Volume
        })
        mock_ticker.history.return_value = incomplete_data
        mock_ticker_class.return_value = mock_ticker

        with pytest.raises((DataValidationError, APIError)):
            fetcher.fetch_ohlcv("AAPL")

    @patch("app.services.data_fetchers.yf.Ticker")
    def test_fetch_network_error(self, mock_ticker_class, fetcher):
        """Test handling of network errors"""
        mock_ticker = Mock()
        mock_ticker.history.side_effect = ConnectionError("Network timeout")
        mock_ticker_class.return_value = mock_ticker

        with pytest.raises(Exception):  # Could be NetworkError
            fetcher.fetch_ohlcv("AAPL")


# Tests for fetch_multiple_tickers
class TestFetchMultipleTickers:
    """Test multiple stock OHLCV fetching"""

    @patch("app.services.data_fetchers.yf.Ticker")
    def test_fetch_multiple_valid_tickers(self, mock_ticker_class, fetcher, sample_ohlcv_data):
        """Test fetching multiple valid tickers"""
        mock_ticker = Mock()
        mock_ticker.history.return_value = sample_ohlcv_data
        mock_ticker_class.return_value = mock_ticker

        results = fetcher.fetch_multiple_tickers(["AAPL", "GOOGL", "MSFT"])

        assert len(results) == 3
        assert "AAPL" in results
        assert "GOOGL" in results
        assert "MSFT" in results

    @patch("app.services.data_fetchers.YahooFinanceFetcher.fetch_ohlcv")
    def test_fetch_multiple_with_failures(self, mock_fetch, fetcher):
        """Test graceful handling of mixed success/failure"""
        # Setup: first succeeds, second fails, third succeeds
        sample_df = pd.DataFrame({
            "Open": [100.0],
            "High": [102.0],
            "Low": [99.0],
            "Close": [101.0],
            "Volume": [1000000]
        })

        mock_fetch.side_effect = [
            sample_df,
            InvalidTickerError("Invalid ticker"),
            sample_df
        ]

        results = fetcher.fetch_multiple_tickers(["AAPL", "INVALID", "MSFT"])

        assert len(results) == 2
        assert "AAPL" in results
        assert "MSFT" in results
        assert "INVALID" not in results


# Tests for validate_data
class TestValidateData:
    """Test data validation"""

    def test_validate_valid_data(self, fetcher, sample_ohlcv_data):
        """Test validation passes for clean data"""
        assert fetcher.validate_data(sample_ohlcv_data) is True

    def test_validate_missing_columns(self, fetcher):
        """Test validation fails for missing columns"""
        incomplete_df = pd.DataFrame({
            "Open": [100.0],
            "High": [102.0],
            "Close": [101.0]
        })

        with pytest.raises(DataValidationError):
            fetcher.validate_data(incomplete_df)

    def test_validate_null_values(self, fetcher):
        """Test validation fails for null values"""
        null_df = pd.DataFrame({
            "Open": [100.0, None],
            "High": [102.0, 104.0],
            "Low": [99.0, 101.0],
            "Close": [101.0, 103.0],
            "Volume": [1000000, 1100000]
        })

        with pytest.raises(DataValidationError):
            fetcher.validate_data(null_df)

    def test_validate_invalid_price_relationship(self, fetcher):
        """Test validation fails for invalid price relationships (high < low)"""
        invalid_df = pd.DataFrame({
            "Open": [100.0],
            "High": [99.0],  # High < Low is invalid
            "Low": [101.0],
            "Close": [100.5],
            "Volume": [1000000]
        })

        with pytest.raises(DataValidationError):
            fetcher.validate_data(invalid_df)

    def test_validate_negative_prices(self, fetcher):
        """Test validation fails for negative prices"""
        negative_df = pd.DataFrame({
            "Open": [-100.0],  # Negative price
            "High": [102.0],
            "Low": [99.0],
            "Close": [101.0],
            "Volume": [1000000]
        })

        with pytest.raises(DataValidationError):
            fetcher.validate_data(negative_df)

    def test_validate_negative_volume(self, fetcher):
        """Test validation fails for negative volume"""
        negative_vol_df = pd.DataFrame({
            "Open": [100.0],
            "High": [102.0],
            "Low": [99.0],
            "Close": [101.0],
            "Volume": [-1000000]  # Negative volume
        })

        with pytest.raises(DataValidationError):
            fetcher.validate_data(negative_vol_df)

    def test_validate_non_numeric_prices(self, fetcher):
        """Test validation fails for non-numeric prices"""
        non_numeric_df = pd.DataFrame({
            "Open": ["100"],  # String instead of numeric
            "High": [102.0],
            "Low": [99.0],
            "Close": [101.0],
            "Volume": [1000000]
        })

        with pytest.raises(DataValidationError):
            fetcher.validate_data(non_numeric_df)


# Tests for save_to_database
class TestSaveToDatabase:
    """Test database storage"""

    def test_save_new_records(self, fetcher, mock_session, sample_ohlcv_data, sample_stock):
        """Test inserting new price records"""
        # Mock for Stock query
        mock_stock_query = Mock()
        mock_stock_query.filter.return_value.first.return_value = sample_stock

        # Mock for StockPrice query
        mock_price_query = Mock()
        mock_price_query.filter.return_value.first.return_value = None

        # Setup query to return different mocks based on model type
        def query_side_effect(model):
            if model == Stock:
                return mock_stock_query
            elif model == StockPrice:
                return mock_price_query
            return Mock()

        mock_session.query.side_effect = query_side_effect

        inserted, updated = fetcher.save_to_database("AAPL", sample_ohlcv_data)

        assert inserted == 10
        assert updated == 0
        mock_session.add.assert_called()
        mock_session.commit.assert_called()

    def test_save_update_existing(self, fetcher, mock_session, sample_ohlcv_data, sample_stock):
        """Test updating existing price records"""
        mock_stock_query = Mock()
        mock_stock_query.filter.return_value.first.return_value = sample_stock

        # Mock price query to return existing records
        mock_price = Mock(spec=StockPrice)
        mock_price_query = Mock()
        mock_price_query.filter.return_value.first.return_value = mock_price

        # Setup session.query to return different mocks based on what's being queried
        def query_side_effect(model):
            if model == Stock:
                return mock_stock_query
            elif model == StockPrice:
                return mock_price_query
            return Mock()

        mock_session.query.side_effect = query_side_effect

        inserted, updated = fetcher.save_to_database("AAPL", sample_ohlcv_data, replace_existing=True)

        assert inserted == 0
        assert updated == 10
        mock_session.commit.assert_called()

    def test_save_invalid_ticker(self, fetcher, mock_session, sample_ohlcv_data):
        """Test error when ticker not found in database"""
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(InvalidTickerError):
            fetcher.save_to_database("AAPL", sample_ohlcv_data)

    def test_save_invalid_data(self, fetcher, mock_session, sample_stock):
        """Test error when data validation fails"""
        invalid_df = pd.DataFrame({
            "Open": [100.0, None],
            "High": [102.0, 104.0],
            "Low": [99.0, 101.0],
            "Close": [101.0, 103.0],
            "Volume": [1000000, 1100000]
        })

        mock_session.query.return_value.filter.return_value.first.return_value = sample_stock

        with pytest.raises(DataValidationError):
            fetcher.save_to_database("AAPL", invalid_df)

    def test_save_database_error(self, fetcher, mock_session, sample_ohlcv_data, sample_stock):
        """Test handling of database errors"""
        mock_session.query.return_value.filter.return_value.first.return_value = sample_stock
        mock_session.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        mock_session.commit.side_effect = Exception("Database error")

        with pytest.raises(DatabaseError):
            fetcher.save_to_database("AAPL", sample_ohlcv_data)

        mock_session.rollback.assert_called()


# Tests for fetch_and_save
class TestFetchAndSave:
    """Test combined fetch and save operations"""

    @patch("app.services.data_fetchers.YahooFinanceFetcher.fetch_ohlcv")
    @patch("app.services.data_fetchers.YahooFinanceFetcher.save_to_database")
    def test_fetch_and_save_success(self, mock_save, mock_fetch, fetcher, sample_ohlcv_data):
        """Test successful fetch and save"""
        mock_fetch.return_value = sample_ohlcv_data
        mock_save.return_value = (10, 0)

        inserted, updated = fetcher.fetch_and_save("AAPL")

        assert inserted == 10
        assert updated == 0
        mock_fetch.assert_called_once()
        mock_save.assert_called_once()

    @patch("app.services.data_fetchers.YahooFinanceFetcher.fetch_ohlcv")
    def test_fetch_and_save_fetch_error(self, mock_fetch, fetcher):
        """Test error handling when fetch fails"""
        mock_fetch.side_effect = InvalidTickerError("Invalid ticker")

        with pytest.raises(InvalidTickerError):
            fetcher.fetch_and_save("INVALID123")


# Tests for fetch_and_save_multiple
class TestFetchAndSaveMultiple:
    """Test batch fetch and save operations"""

    @patch("app.services.data_fetchers.YahooFinanceFetcher.fetch_and_save")
    def test_fetch_and_save_multiple_success(self, mock_fetch_save, fetcher):
        """Test successful batch fetch and save"""
        mock_fetch_save.side_effect = [(10, 0), (10, 0), (10, 0)]

        results = fetcher.fetch_and_save_multiple(["AAPL", "GOOGL", "MSFT"])

        assert len(results) == 3
        assert results["AAPL"] == (10, 0)
        assert results["GOOGL"] == (10, 0)
        assert results["MSFT"] == (10, 0)

    @patch("app.services.data_fetchers.YahooFinanceFetcher.fetch_and_save")
    def test_fetch_and_save_multiple_with_failures(self, mock_fetch_save, fetcher):
        """Test batch operation continues despite failures"""
        mock_fetch_save.side_effect = [
            (10, 0),
            Exception("API error"),
            (10, 0)
        ]

        results = fetcher.fetch_and_save_multiple(["AAPL", "INVALID", "MSFT"])

        assert len(results) == 3
        assert results["AAPL"] == (10, 0)
        assert results["INVALID"] == (0, 0)  # Marked as failed
        assert results["MSFT"] == (10, 0)


# Integration-like tests
class TestDataFetcherIntegration:
    """Integration tests with database"""

    @pytest.mark.skip(reason="SQLite integration test - requires BigInteger sequence support")
    def test_save_to_real_database(self, db, sample_ohlcv_data):
        """Test saving to real (test) database"""
        # Create a stock record first
        stock = Stock(ticker="AAPL", market="NYSE")
        db.add(stock)
        db.commit()

        # Now test the fetcher
        fetcher = YahooFinanceFetcher(db)
        inserted, updated = fetcher.save_to_database("AAPL", sample_ohlcv_data)

        assert inserted == 10
        assert updated == 0

        # Verify records were saved
        prices = db.query(StockPrice).filter(
            StockPrice.stock_id == stock.id
        ).all()
        assert len(prices) == 10

        # Verify data integrity
        first_price = prices[0]
        assert first_price.open_price == 100.0
        assert first_price.close_price == 101.5
        assert first_price.volume == 1000000
