"""
NewsAPI Data Fetcher Service
Handles retrieval and storage of news articles from NewsAPI.org
"""

import logging
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.exceptions import (
    APIError,
    DataValidationError,
    DatabaseError,
    RateLimitError,
    NetworkError,
)
from app.config import settings

if TYPE_CHECKING:
    from app.models.stock import Stock
    from app.models.news import NewsEvent

# Configure logging
logger = logging.getLogger(__name__)

# NewsAPI constants
NEWSAPI_BASE_URL = "https://newsapi.org/v2"
NEWSAPI_ENDPOINT = f"{NEWSAPI_BASE_URL}/everything"
DEFAULT_DAYS_BACK = 7
API_RATE_LIMIT_REQUESTS = 100
API_RATE_LIMIT_PERIOD = "day"


class NewsAPIFetcher:
    """
    Fetches news articles about stocks from NewsAPI and stores in database.

    Features:
    - Fetch news articles for single or multiple stocks
    - Search by stock ticker and company name
    - Filter by date range and relevance
    - Deduplication based on content hash
    - Batch insert with error handling
    - Rate limiting and quota monitoring
    - Comprehensive error handling with custom exceptions
    """

    def __init__(self, session: Session, api_key: Optional[str] = None):
        """
        Initialize the NewsAPI fetcher.

        Args:
            session: SQLAlchemy database session
            api_key: NewsAPI key (defaults to NEWSAPI_KEY env var)

        Raises:
            APIError: If API key is missing
        """
        self.session = session
        self.api_key = api_key or settings.NEWSAPI_KEY
        self.logger = logger
        self.base_url = NEWSAPI_ENDPOINT

        if not self.api_key:
            raise APIError(
                "NewsAPI key not configured. Set NEWSAPI_KEY environment variable."
            )

        # Validate API key format (basic check)
        if len(self.api_key.strip()) < 10:
            raise APIError("Invalid NewsAPI key format")

        self.logger.info("NewsAPIFetcher initialized successfully")

    def fetch_news(
        self,
        stock_ticker: str,
        company_name: Optional[str] = None,
        days_back: int = DEFAULT_DAYS_BACK,
        language: str = "en",
        sort_by: str = "relevancy",
    ) -> List[Dict]:
        """
        Fetch news articles for a single stock.

        Args:
            stock_ticker: Stock ticker symbol (e.g., 'AAPL')
            company_name: Full company name (optional, used if provided)
            days_back: Number of days to look back (default: 7)
            language: News language (default: 'en')
            sort_by: Sort order - 'relevancy', 'popularity', 'publishedAt'

        Returns:
            List of article dictionaries with keys:
            - title, description, content, url, source, published_at, image_url

        Raises:
            APIError: If API request fails
            RateLimitError: If rate limit exceeded
            NetworkError: If network error occurs
            DataValidationError: If parameters invalid
        """
        # Validate inputs
        if not stock_ticker or len(stock_ticker) > 20:
            raise DataValidationError(f"Invalid ticker format: {stock_ticker}")

        if days_back < 1 or days_back > 365:
            raise DataValidationError(
                f"days_back must be between 1 and 365, got {days_back}"
            )

        # Build search query
        search_terms = [stock_ticker.upper()]
        if company_name:
            search_terms.append(company_name)

        query = " OR ".join(search_terms)
        from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime(
            "%Y-%m-%d"
        )

        try:
            self.logger.info(
                f"Fetching news for {stock_ticker} from {from_date}, query='{query}'"
            )

            # Make API request
            response = requests.get(
                self.base_url,
                params={
                    "q": query,
                    "from": from_date,
                    "language": language,
                    "sortBy": sort_by,
                    "apiKey": self.api_key,
                },
                timeout=30,
            )

            # Handle rate limiting
            if response.status_code == 429:
                self.logger.error(
                    "NewsAPI rate limit exceeded. Free tier: 100 requests/day"
                )
                raise RateLimitError(
                    "NewsAPI rate limit exceeded. Max 100 requests per day on free tier."
                )

            # Handle authentication errors
            if response.status_code == 401:
                self.logger.error("Invalid NewsAPI key")
                raise APIError("Invalid or expired NewsAPI key")

            # Handle other HTTP errors
            if response.status_code not in (200, 202):
                self.logger.error(
                    f"NewsAPI request failed with status {response.status_code}: {response.text}"
                )
                raise APIError(
                    f"NewsAPI returned status {response.status_code}: {response.text}"
                )

            # Parse response
            data = response.json()

            # Check for API-level errors (e.g., invalid parameters)
            if data.get("status") != "ok":
                error_code = data.get("code", "unknown")
                error_message = data.get("message", "Unknown error")
                self.logger.error(
                    f"NewsAPI error - {error_code}: {error_message}"
                )

                if error_code == "apiKeyExhausted":
                    raise RateLimitError("NewsAPI quota exhausted")
                elif error_code == "apiKeyInvalid":
                    raise APIError("Invalid NewsAPI key")
                else:
                    raise APIError(f"NewsAPI error: {error_message}")

            articles = data.get("articles", [])
            self.logger.info(
                f"Successfully fetched {len(articles)} articles for {stock_ticker}"
            )

            # Transform articles to standardized format
            return self._transform_articles(articles)

        except (RateLimitError, APIError):
            # Re-raise API errors without wrapping
            raise

        except requests.Timeout:
            self.logger.error(f"Timeout fetching news for {stock_ticker}")
            raise NetworkError(
                f"Timeout while fetching news for {stock_ticker} after 30 seconds"
            )

        except requests.ConnectionError as e:
            self.logger.error(f"Connection error fetching news for {stock_ticker}: {e}")
            raise NetworkError(
                f"Network error while fetching news for {stock_ticker}"
            ) from e

        except requests.RequestException as e:
            self.logger.error(f"Request error fetching news for {stock_ticker}: {e}")
            raise NetworkError(f"Request failed for {stock_ticker}") from e

        except Exception as e:
            self.logger.error(f"Unexpected error fetching news for {stock_ticker}: {e}")
            raise APIError(f"Failed to fetch news for {stock_ticker}: {str(e)}") from e

    def fetch_multiple_stocks(
        self,
        tickers: List[str],
        company_names: Optional[Dict[str, str]] = None,
        days_back: int = DEFAULT_DAYS_BACK,
    ) -> Dict[str, List[Dict]]:
        """
        Fetch news for multiple stocks.

        Args:
            tickers: List of ticker symbols
            company_names: Dict mapping ticker to company name (optional)
            days_back: Number of days to look back

        Returns:
            Dictionary mapping ticker to list of articles

        Note:
            Continues processing even if some tickers fail.
        """
        company_names = company_names or {}
        results = {}
        failures = []

        self.logger.info(f"Fetching news for {len(tickers)} tickers")

        for ticker in tickers:
            try:
                company_name = company_names.get(ticker)
                articles = self.fetch_news(ticker, company_name, days_back)
                results[ticker] = articles

            except RateLimitError as e:
                # Stop if we hit rate limit - don't waste more requests
                self.logger.error(f"Rate limit hit while fetching {ticker}: {e}")
                failures.append((ticker, "RateLimitError", str(e)))
                raise

            except (APIError, NetworkError) as e:
                self.logger.warning(f"Failed to fetch {ticker}: {str(e)}")
                failures.append((ticker, type(e).__name__, str(e)))

        if failures:
            self.logger.warning(
                f"Failed to fetch {len(failures)} out of {len(tickers)} tickers"
            )

        self.logger.info(f"Successfully fetched {len(results)} out of {len(tickers)} tickers")
        return results

    def _transform_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Transform raw NewsAPI articles to standardized format.

        Args:
            articles: Raw article list from NewsAPI

        Returns:
            List of standardized article dictionaries
        """
        transformed = []

        for article in articles:
            # Ensure minimum required fields
            if not article.get("title") or not article.get("url"):
                self.logger.debug("Skipping article missing title or URL")
                continue

            transformed_article = {
                "title": article.get("title", ""),
                "description": article.get("description") or "",
                "content": article.get("content") or "",
                "url": article.get("url", ""),
                "source_name": article.get("source", {}).get("name", "Unknown"),
                "published_at": article.get("publishedAt", ""),
                "image_url": article.get("urlToImage") or "",
                "author": article.get("author") or "",
            }

            transformed.append(transformed_article)

        return transformed

    def validate_article(self, article: Dict) -> bool:
        """
        Validate an article has required fields for database storage.

        Args:
            article: Article dictionary

        Returns:
            True if valid

        Raises:
            DataValidationError: If validation fails
        """
        required_fields = ["title", "url", "source_name"]

        missing_fields = [f for f in required_fields if not article.get(f)]
        if missing_fields:
            raise DataValidationError(
                f"Article missing required fields: {missing_fields}"
            )

        # Validate URL format (basic check)
        url = article.get("url", "")
        if not url.startswith("http://") and not url.startswith("https://"):
            raise DataValidationError(f"Invalid URL format: {url}")

        # Validate title length
        title = article.get("title", "")
        if len(title) > 500:
            raise DataValidationError(
                f"Title too long: {len(title)} chars (max 500)"
            )

        return True

    def calculate_content_hash(self, article: Dict) -> str:
        """
        Calculate hash for article deduplication.

        Uses SHA256 hash of title + content to detect duplicates.

        Args:
            article: Article dictionary

        Returns:
            SHA256 hash string
        """
        # Combine title and content for hash
        title = article.get("title", "")
        content = article.get("content", "") or article.get("description", "")

        hash_input = f"{title}||{content}".lower().strip()
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()

        return hash_value

    def save_to_database(
        self,
        stock_id: int,
        articles: List[Dict],
    ) -> Tuple[int, int]:
        """
        Save articles to database with deduplication.

        Args:
            stock_id: ID of the stock to associate articles with
            articles: List of article dictionaries

        Returns:
            Tuple of (inserted_count, skipped_duplicates)

        Raises:
            DatabaseError: If database operation fails
        """
        from app.models.news import NewsEvent

        inserted_count = 0
        skipped_duplicates = 0

        try:
            for article in articles:
                # Validate article
                try:
                    self.validate_article(article)
                except DataValidationError as e:
                    self.logger.warning(f"Skipping invalid article: {e}")
                    continue

                # Calculate hash for deduplication
                content_hash = self.calculate_content_hash(article)

                # Check if article already exists
                existing = self.session.query(NewsEvent).filter(
                    and_(
                        NewsEvent.stock_id == stock_id,
                        NewsEvent.content_hash == content_hash,
                    )
                ).first()

                if existing:
                    self.logger.debug(
                        f"Skipping duplicate article: {article.get('title', '')[:50]}"
                    )
                    skipped_duplicates += 1
                    continue

                # Parse published_at date
                published_at = None
                try:
                    published_str = article.get("published_at", "")
                    if published_str:
                        # Handle ISO format with timezone
                        if "T" in published_str:
                            published_at = datetime.fromisoformat(
                                published_str.replace("Z", "+00:00")
                            )
                except Exception as e:
                    self.logger.warning(
                        f"Could not parse published_at: {article.get('published_at')}: {e}"
                    )

                # Create news event record
                news_event = NewsEvent(
                    stock_id=stock_id,
                    headline=article.get("title", "")[:500],
                    content=article.get("content", "")
                    or article.get("description", ""),
                    source_name=article.get("source_name", "")[:100],
                    original_url=article.get("url", "")[:500],
                    published_at=published_at,
                    content_hash=content_hash,
                    fetched_at=datetime.utcnow(),
                    event_date=published_at.date() if published_at else datetime.utcnow().date(),
                    event_category="news",  # Default category, can be refined in STORY_3_1
                )

                self.session.add(news_event)
                inserted_count += 1

            # Commit all changes
            self.session.commit()

            self.logger.info(
                f"Saved articles: {inserted_count} inserted, {skipped_duplicates} duplicates skipped"
            )

            return inserted_count, skipped_duplicates

        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Database error saving articles: {str(e)}")
            raise DatabaseError(f"Failed to save articles to database: {str(e)}") from e

    def fetch_and_save(
        self,
        stock_ticker: str,
        stock_id: int,
        company_name: Optional[str] = None,
        days_back: int = DEFAULT_DAYS_BACK,
    ) -> Tuple[int, int]:
        """
        Convenience method: Fetch articles and immediately save to database.

        Args:
            stock_ticker: Stock ticker symbol
            stock_id: Database ID of the stock
            company_name: Company name (optional)
            days_back: Number of days to look back

        Returns:
            Tuple of (inserted_count, skipped_duplicates)

        Raises:
            Various exceptions from fetch_news and save_to_database
        """
        articles = self.fetch_news(stock_ticker, company_name, days_back)
        return self.save_to_database(stock_id, articles)

    def fetch_and_save_multiple(
        self,
        stock_data: List[Dict],
        days_back: int = DEFAULT_DAYS_BACK,
    ) -> Dict[str, Tuple[int, int]]:
        """
        Fetch and save news for multiple stocks.

        Args:
            stock_data: List of dicts with 'ticker', 'id', and optional 'name'
            days_back: Number of days to look back

        Returns:
            Dictionary mapping ticker to (inserted_count, skipped_duplicates)

        Note:
            Continues processing even if some stocks fail.
        """
        results = {}

        for stock_info in stock_data:
            ticker = stock_info.get("ticker")
            stock_id = stock_info.get("id")
            company_name = stock_info.get("name")

            if not ticker or not stock_id:
                self.logger.warning(f"Skipping invalid stock_data entry: {stock_info}")
                continue

            try:
                inserted, skipped = self.fetch_and_save(
                    ticker, stock_id, company_name, days_back
                )
                results[ticker] = (inserted, skipped)

            except RateLimitError as e:
                # Stop if rate limit hit
                self.logger.error(f"Rate limit hit while fetching {ticker}: {e}")
                results[ticker] = (0, 0)
                raise

            except Exception as e:
                self.logger.error(
                    f"Failed to fetch and save {ticker}: {str(e)}"
                )
                results[ticker] = (0, 0)

        return results
