"""
Custom Exception Classes for Stock Predictor Application
"""
from datetime import datetime


class StockPredictorException(Exception):
    """Base exception for all Stock Predictor errors"""
    def __init__(self, message: str, code: str = None, status_code: int = 500):
        self.message = message
        self.code = code or self.__class__.__name__
        self.status_code = status_code
        self.timestamp = datetime.utcnow().isoformat()
        super().__init__(self.message)

    def to_dict(self):
        """Convert exception to dictionary for API response"""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "timestamp": self.timestamp
            }
        }


class ValidationError(StockPredictorException):
    """Raised when input validation fails"""
    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        super().__init__(message, code, 400)


class InvalidStockSymbolError(ValidationError):
    """Raised when stock symbol is invalid"""
    def __init__(self, symbol: str):
        super().__init__(
            f"Invalid stock symbol: '{symbol}'. Must be 1-5 uppercase letters.",
            "INVALID_SYMBOL"
        )


class InsufficientDataError(ValidationError):
    """Raised when required data is missing"""
    def __init__(self, field: str):
        super().__init__(
            f"Required field missing: '{field}'",
            "MISSING_REQUIRED_FIELD"
        )


class DuplicateError(ValidationError):
    """Raised when duplicate record attempted"""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            f"{resource} already exists: {identifier}",
            "DUPLICATE_RESOURCE"
        )


class NotFoundError(StockPredictorException):
    """Raised when resource not found"""
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, "NOT_FOUND", 404)


class AuthenticationError(StockPredictorException):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, "AUTHENTICATION_REQUIRED", 401)


class AuthorizationError(StockPredictorException):
    """Raised when user doesn't have permission"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "PERMISSION_DENIED", 403)


class InvalidTickerError(ValidationError):
    """Raised when a stock ticker is invalid or not found"""
    def __init__(self, ticker: str):
        super().__init__(
            f"Invalid or unknown stock ticker: {ticker}",
            "INVALID_TICKER"
        )


class APIError(StockPredictorException):
    """Raised when an external API call fails"""
    def __init__(self, api_name: str, status_code: int = None, message: str = None):
        msg = f"External API error: {api_name}"
        if status_code:
            msg += f" (status: {status_code})"
        if message:
            msg += f": {message}"
        super().__init__(msg, "EXTERNAL_API_ERROR", 502)


class DataValidationError(ValidationError):
    """Raised when data validation fails"""
    pass


class DatabaseError(StockPredictorException):
    """Raised when a database operation fails"""
    def __init__(self, message: str = "Database operation failed", operation: str = None):
        msg = message
        if operation:
            msg += f" ({operation})"
        super().__init__(msg, "DATABASE_ERROR", 500)


class RateLimitError(StockPredictorException):
    """Raised when API rate limit is hit"""
    def __init__(self, message: str = "Rate limit exceeded", limit: str = None):
        msg = message
        if limit:
            msg += f": {limit}"
        super().__init__(msg, "RATE_LIMIT_EXCEEDED", 429)


class NetworkError(APIError):
    """Raised when network connectivity issues occur"""
    def __init__(self, message: str = "Network connection failed"):
        super().__init__("Network", message=message)
        self.code = "NETWORK_ERROR"


class ConfigurationError(StockPredictorException):
    """Raised when configuration is invalid"""
    def __init__(self, message: str):
        super().__init__(message, "CONFIGURATION_ERROR", 500)


class DataRetrievalError(StockPredictorException):
    """Raised when data retrieval fails"""
    def __init__(self, source: str, message: str = None):
        msg = f"Failed to retrieve data from {source}"
        if message:
            msg += f": {message}"
        super().__init__(msg, "DATA_RETRIEVAL_FAILED", 502)
