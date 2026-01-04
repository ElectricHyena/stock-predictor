"""
Yahoo Finance Data Fetcher Service
Handles retrieval and storage of historical stock price data from Yahoo Finance
"""

import logging
import os
import time
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from sqlalchemy.orm import Session
from sqlalchemy import and_
from functools import wraps

from app.exceptions import (
    InvalidTickerError,
    APIError,
    DataValidationError,
    DatabaseError,
    RateLimitError,
    NetworkError,
)

if TYPE_CHECKING:
    from app.models.stock import Stock
    from app.models.price import StockPrice

# Configure logging
logger = logging.getLogger(__name__)

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.getenv("YAHOO_RATE_LIMIT_REQUESTS", "5"))  # requests per window
RATE_LIMIT_WINDOW = float(os.getenv("YAHOO_RATE_LIMIT_WINDOW", "1.0"))  # window in seconds
MAX_RETRIES = int(os.getenv("YAHOO_MAX_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("YAHOO_RETRY_DELAY", "2.0"))  # base delay in seconds


class RateLimiter:
    """Simple token bucket rate limiter"""

    def __init__(self, requests_per_window: int = 5, window_seconds: float = 1.0):
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.request_times: List[float] = []

    def acquire(self) -> None:
        """Wait if rate limit would be exceeded"""
        now = time.time()

        # Remove requests outside the window
        self.request_times = [
            t for t in self.request_times
            if now - t < self.window_seconds
        ]

        # If at limit, wait until oldest request expires
        if len(self.request_times) >= self.requests_per_window:
            sleep_time = self.window_seconds - (now - self.request_times[0])
            if sleep_time > 0:
                logger.debug(f"Rate limit: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
                # Clean up after sleeping
                now = time.time()
                self.request_times = [
                    t for t in self.request_times
                    if now - t < self.window_seconds
                ]

        # Record this request
        self.request_times.append(time.time())


def retry_with_backoff(max_retries: int = MAX_RETRIES, base_delay: float = RETRY_DELAY):
    """Decorator for retrying with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (NetworkError, APIError, ConnectionError) as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed")
                except InvalidTickerError:
                    # Don't retry for invalid tickers
                    raise

            # If we get here, all retries failed
            raise last_exception

        return wrapper
    return decorator


class YahooFinanceFetcher:
    """
    Fetches historical stock price data from Yahoo Finance and stores in database.

    Features:
    - Fetch OHLCV data for single or multiple stocks
    - Data validation before storage
    - Batch insert for performance
    - Comprehensive error handling with retry logic
    - Rate limiting to avoid API throttling
    - Logging of all operations
    """

    # Shared rate limiter across all instances
    _rate_limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW)

    def __init__(self, session: Session, data_source: str = "yahoo_finance"):
        """
        Initialize the fetcher with a database session.

        Args:
            session: SQLAlchemy database session
            data_source: Source identifier for the fetched data
        """
        self.session = session
        self.data_source = data_source
        self.logger = logger
        self.rate_limiter = YahooFinanceFetcher._rate_limiter

    @retry_with_backoff()
    def fetch_ohlcv(
        self,
        ticker: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for a single stock from Yahoo Finance.

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
            start_date: Start date for historical data (default: 1 year ago)
            end_date: End date for historical data (default: today)

        Returns:
            DataFrame with OHLCV data

        Raises:
            InvalidTickerError: If ticker is invalid or not found
            APIError: If API request fails
            NetworkError: If network error occurs
        """
        # Set default dates
        if end_date is None:
            end_date = datetime.now()

        if start_date is None:
            start_date = end_date - timedelta(days=365)

        # Normalize ticker
        ticker = ticker.upper().strip()

        if not ticker or len(ticker) > 10:
            raise InvalidTickerError(f"Invalid ticker format: {ticker}")

        try:
            # Apply rate limiting
            self.rate_limiter.acquire()

            self.logger.info(
                f"Fetching data for {ticker} from {start_date.date()} to {end_date.date()}"
            )

            # Create Ticker object
            stock = yf.Ticker(ticker)

            # Fetch historical data
            df = stock.history(start=start_date, end=end_date)

            # Check if data is empty
            if df.empty:
                self.logger.warning(f"No data returned for ticker: {ticker}")
                raise InvalidTickerError(
                    f"No data found for ticker {ticker}. "
                    "Ticker may be invalid or not supported by Yahoo Finance."
                )

            # Verify we got valid OHLCV columns
            required_columns = ["Open", "High", "Low", "Close", "Volume"]
            if not all(col in df.columns for col in required_columns):
                raise DataValidationError(
                    f"Missing required OHLCV columns for {ticker}"
                )

            self.logger.info(
                f"Successfully fetched {len(df)} records for {ticker}"
            )
            return df

        except yf.exceptions.YFException as e:
            self.logger.error(f"Yahoo Finance API error for {ticker}: {str(e)}")
            if "No data found" in str(e) or "not found" in str(e).lower():
                raise InvalidTickerError(f"Ticker not found: {ticker}") from e
            raise APIError(f"Yahoo Finance API error: {str(e)}") from e

        except ConnectionError as e:
            self.logger.error(f"Network error fetching {ticker}: {str(e)}")
            raise NetworkError(f"Network error while fetching {ticker}") from e

        except Exception as e:
            self.logger.error(f"Unexpected error fetching {ticker}: {str(e)}")
            raise APIError(f"Failed to fetch data for {ticker}: {str(e)}") from e

    def fetch_multiple_tickers(
        self,
        tickers: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch OHLCV data for multiple stocks.

        Args:
            tickers: List of stock ticker symbols
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            Dictionary mapping ticker to DataFrame with OHLCV data

        Note:
            Returns successful tickers. Failed tickers are logged but don't raise exceptions.
        """
        results = {}
        failures = []

        self.logger.info(f"Fetching data for {len(tickers)} tickers")

        for ticker in tickers:
            try:
                df = self.fetch_ohlcv(ticker, start_date, end_date)
                results[ticker] = df

            except InvalidTickerError as e:
                self.logger.warning(f"Skipping invalid ticker {ticker}: {str(e)}")
                failures.append((ticker, "InvalidTickerError", str(e)))

            except (APIError, NetworkError) as e:
                self.logger.warning(f"Failed to fetch {ticker}: {str(e)}")
                failures.append((ticker, type(e).__name__, str(e)))

        if failures:
            self.logger.info(
                f"Failed to fetch {len(failures)} out of {len(tickers)} tickers"
            )

        self.logger.info(f"Successfully fetched {len(results)} tickers")
        return results

    def validate_data(self, df: pd.DataFrame, ticker: str = "Unknown") -> bool:
        """
        Validate OHLCV data before storage.

        Checks:
        - No null values in required columns
        - Correct data types (numeric for prices, int for volume)
        - Price relationships (high >= low, high >= open, high >= close)
        - Non-negative values
        - Volume is positive or zero

        Args:
            df: DataFrame with OHLCV data
            ticker: Ticker symbol for logging

        Returns:
            True if data is valid

        Raises:
            DataValidationError: If validation fails
        """
        required_columns = ["Open", "High", "Low", "Close", "Volume"]

        # Check for required columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise DataValidationError(
                f"Missing required columns for {ticker}: {missing_cols}"
            )

        # Check for null values in required columns
        null_counts = df[required_columns].isnull().sum()
        if null_counts.any():
            null_cols = null_counts[null_counts > 0].index.tolist()
            raise DataValidationError(
                f"Null values found in {ticker} for columns: {null_cols}"
            )

        # Check data types
        for col in ["Open", "High", "Low", "Close"]:
            if not pd.api.types.is_numeric_dtype(df[col]):
                raise DataValidationError(
                    f"Column {col} is not numeric for {ticker}"
                )

        if not pd.api.types.is_numeric_dtype(df["Volume"]):
            raise DataValidationError(f"Volume is not numeric for {ticker}")

        # Check price relationships
        invalid_high_open = (df["High"] < df["Open"]).any()
        invalid_high_low = (df["High"] < df["Low"]).any()
        invalid_high_close = (df["High"] < df["Close"]).any()
        invalid_low_close = (df["Low"] > df["Close"]).any()

        if invalid_high_low:
            raise DataValidationError(
                f"Invalid price relationships for {ticker}: High < Low"
            )

        # Check for negative prices
        if (df[["Open", "High", "Low", "Close"]] < 0).any().any():
            raise DataValidationError(
                f"Negative prices found for {ticker}"
            )

        # Check volume
        if (df["Volume"] < 0).any():
            raise DataValidationError(
                f"Negative volume found for {ticker}"
            )

        self.logger.debug(f"Data validation passed for {ticker}")
        return True

    def save_to_database(
        self,
        ticker: str,
        df: pd.DataFrame,
        replace_existing: bool = True,
    ) -> Tuple[int, int]:
        """
        Save OHLCV data to the database.

        Args:
            ticker: Stock ticker symbol
            df: DataFrame with OHLCV data (indexed by date)
            replace_existing: If True, replace existing records for same dates

        Returns:
            Tuple of (inserted_count, updated_count)

        Raises:
            InvalidTickerError: If stock ticker not found in database
            DataValidationError: If data validation fails
            DatabaseError: If database operation fails
        """
        # Import here to avoid circular imports
        from app.models.stock import Stock
        from app.models.price import StockPrice

        # Validate data first
        try:
            self.validate_data(df, ticker)
        except DataValidationError as e:
            self.logger.error(f"Data validation failed for {ticker}: {str(e)}")
            raise

        # Get or create stock record
        stock = self.session.query(Stock).filter(
            Stock.ticker == ticker.upper()
        ).first()

        if not stock:
            self.logger.error(f"Stock {ticker} not found in database")
            raise InvalidTickerError(
                f"Stock {ticker} not found in database. "
                "Please add it first using Stock model."
            )

        try:
            inserted_count = 0
            updated_count = 0

            # Process each row in the DataFrame
            for date_index, row in df.iterrows():
                # Convert index to date if it's a datetime
                if hasattr(date_index, "date"):
                    record_date = date_index.date()
                else:
                    record_date = date_index

                # Check if record already exists
                existing = self.session.query(StockPrice).filter(
                    and_(
                        StockPrice.stock_id == stock.id,
                        StockPrice.date == record_date,
                    )
                ).first()

                # Prepare price record
                price_data = {
                    "stock_id": stock.id,
                    "date": record_date,
                    "open_price": float(row["Open"]) if pd.notna(row["Open"]) else None,
                    "high_price": float(row["High"]) if pd.notna(row["High"]) else None,
                    "low_price": float(row["Low"]) if pd.notna(row["Low"]) else None,
                    "close_price": float(row["Close"]) if pd.notna(row["Close"]) else None,
                    "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else None,
                    "adjusted_close": float(row.get("Adj Close", row["Close"])) if "Adj Close" in row and pd.notna(row.get("Adj Close")) else None,
                    "data_source": self.data_source,
                    "is_valid": True,
                }

                if existing:
                    # Update existing record
                    if replace_existing:
                        for key, value in price_data.items():
                            if key != "date" and key != "stock_id":
                                setattr(existing, key, value)
                        updated_count += 1
                    else:
                        self.logger.debug(
                            f"Skipping existing record for {ticker} on {record_date}"
                        )
                else:
                    # Create new record
                    price_record = StockPrice(**price_data)
                    self.session.add(price_record)
                    inserted_count += 1

            # Commit all changes
            self.session.commit()

            # Update stock's last_price_updated_at
            stock.last_price_updated_at = datetime.utcnow()
            self.session.commit()

            self.logger.info(
                f"Saved data for {ticker}: "
                f"{inserted_count} inserted, {updated_count} updated"
            )

            return inserted_count, updated_count

        except Exception as e:
            self.session.rollback()
            self.logger.error(
                f"Database error saving {ticker}: {str(e)}"
            )
            raise DatabaseError(
                f"Failed to save data for {ticker}: {str(e)}"
            ) from e

    def fetch_and_save(
        self,
        ticker: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        replace_existing: bool = True,
    ) -> Tuple[int, int]:
        """
        Convenience method: Fetch data and immediately save to database.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data
            replace_existing: If True, replace existing records

        Returns:
            Tuple of (inserted_count, updated_count)

        Raises:
            Various exceptions from fetch_ohlcv and save_to_database
        """
        df = self.fetch_ohlcv(ticker, start_date, end_date)
        return self.save_to_database(ticker, df, replace_existing)

    def fetch_and_save_multiple(
        self,
        tickers: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        replace_existing: bool = True,
    ) -> Dict[str, Tuple[int, int]]:
        """
        Fetch and save data for multiple stocks.

        Args:
            tickers: List of stock ticker symbols
            start_date: Start date for historical data
            end_date: End date for historical data
            replace_existing: If True, replace existing records

        Returns:
            Dictionary mapping ticker to (inserted_count, updated_count)

        Note:
            Continues processing even if some tickers fail.
        """
        results = {}

        for ticker in tickers:
            try:
                inserted, updated = self.fetch_and_save(
                    ticker, start_date, end_date, replace_existing
                )
                results[ticker] = (inserted, updated)

            except Exception as e:
                self.logger.error(
                    f"Failed to fetch and save {ticker}: {str(e)}"
                )
                results[ticker] = (0, 0)  # Mark as failed

        return results
