"""
Unit Tests for Error Handling and Validation
"""
import pytest
from app.exceptions import (
    InvalidStockSymbolError,
    ValidationError,
    NotFoundError,
    InsufficientDataError,
    AuthenticationError,
    RateLimitError,
    DatabaseError
)
from app.validators import Validators


class TestCustomExceptions:
    """Test custom exception classes"""

    def test_invalid_stock_symbol_error(self):
        """Test InvalidStockSymbolError exception"""
        with pytest.raises(InvalidStockSymbolError) as exc_info:
            raise InvalidStockSymbolError("INVALID123")

        assert exc_info.value.code == "INVALID_SYMBOL"
        assert exc_info.value.status_code == 400
        assert "Invalid stock symbol" in exc_info.value.message

    def test_not_found_error(self):
        """Test NotFoundError exception"""
        with pytest.raises(NotFoundError) as exc_info:
            raise NotFoundError("Stock", "AAPL")

        assert exc_info.value.code == "NOT_FOUND"
        assert exc_info.value.status_code == 404
        assert "AAPL" in exc_info.value.message

    def test_authentication_error(self):
        """Test AuthenticationError exception"""
        with pytest.raises(AuthenticationError) as exc_info:
            raise AuthenticationError()

        assert exc_info.value.code == "AUTHENTICATION_REQUIRED"
        assert exc_info.value.status_code == 401

    def test_rate_limit_error(self):
        """Test RateLimitError exception"""
        with pytest.raises(RateLimitError) as exc_info:
            raise RateLimitError("Rate limit exceeded", "100/hour")

        assert exc_info.value.code == "RATE_LIMIT_EXCEEDED"
        assert exc_info.value.status_code == 429

    def test_database_error(self):
        """Test DatabaseError exception"""
        with pytest.raises(DatabaseError) as exc_info:
            raise DatabaseError("Query failed", "SELECT")

        assert exc_info.value.code == "DATABASE_ERROR"
        assert exc_info.value.status_code == 500

    def test_exception_to_dict(self):
        """Test exception conversion to dict"""
        error = InvalidStockSymbolError("TEST")
        error_dict = error.to_dict()

        assert "error" in error_dict
        assert error_dict["error"]["code"] == "INVALID_SYMBOL"
        assert "message" in error_dict["error"]
        assert "timestamp" in error_dict["error"]


class TestValidators:
    """Test input validators"""

    def test_validate_stock_symbol_valid(self):
        """Test valid stock symbol validation"""
        result = Validators.validate_stock_symbol("AAPL")
        assert result == "AAPL"

    def test_validate_stock_symbol_lowercase(self):
        """Test stock symbol conversion to uppercase"""
        result = Validators.validate_stock_symbol("aapl")
        assert result == "AAPL"

    def test_validate_stock_symbol_invalid(self):
        """Test invalid stock symbol validation"""
        with pytest.raises(InvalidStockSymbolError):
            Validators.validate_stock_symbol("INVALID123")

    def test_validate_stock_symbol_empty(self):
        """Test empty stock symbol validation"""
        with pytest.raises(InsufficientDataError):
            Validators.validate_stock_symbol("")

    def test_validate_email_valid(self):
        """Test valid email validation"""
        result = Validators.validate_email("test@example.com")
        assert result == "test@example.com"

    def test_validate_email_invalid(self):
        """Test invalid email validation"""
        with pytest.raises(ValidationError):
            Validators.validate_email("invalid-email")

    def test_validate_numeric_range_valid(self):
        """Test valid numeric range validation"""
        result = Validators.validate_numeric_range(5.0, min_value=0, max_value=10)
        assert result == 5.0

    def test_validate_numeric_range_below_min(self):
        """Test numeric value below minimum"""
        with pytest.raises(ValidationError):
            Validators.validate_numeric_range(-1, min_value=0, max_value=10)

    def test_validate_numeric_range_above_max(self):
        """Test numeric value above maximum"""
        with pytest.raises(ValidationError):
            Validators.validate_numeric_range(11, min_value=0, max_value=10)

    def test_validate_string_valid(self):
        """Test valid string validation"""
        result = Validators.validate_string("test", field_name="name")
        assert result == "test"

    def test_validate_string_too_short(self):
        """Test string below minimum length"""
        with pytest.raises(ValidationError):
            Validators.validate_string("", field_name="name", min_length=1)

    def test_validate_string_too_long(self):
        """Test string exceeds maximum length"""
        with pytest.raises(ValidationError):
            Validators.validate_string("a" * 100, field_name="name", max_length=50)

    def test_validate_enum_valid(self):
        """Test valid enum validation"""
        result = Validators.validate_enum("active", ["active", "inactive"])
        assert result == "active"

    def test_validate_enum_invalid(self):
        """Test invalid enum value"""
        with pytest.raises(ValidationError):
            Validators.validate_enum("invalid", ["active", "inactive"])

    def test_sanitize_input_removes_script_tags(self):
        """Test sanitization removes script tags"""
        result = Validators.sanitize_input("<script>alert('xss')</script>Hello")
        assert "<script>" not in result
        assert "Hello" in result

    def test_sanitize_input_removes_event_handlers(self):
        """Test sanitization removes event handlers"""
        result = Validators.sanitize_input('<img src="x" onerror="alert(1)">')
        assert "onerror" not in result

    def test_sanitize_input_removes_iframes(self):
        """Test sanitization removes iframe tags"""
        result = Validators.sanitize_input('<iframe src="evil.com"></iframe>')
        assert "<iframe" not in result

    def test_validate_integer_valid(self):
        """Test valid integer validation"""
        result = Validators.validate_integer(42)
        assert result == 42

    def test_validate_integer_invalid(self):
        """Test invalid integer validation"""
        with pytest.raises(ValidationError):
            Validators.validate_integer("not_an_int")


@pytest.mark.integration
class TestErrorHandlerMiddleware:
    """Test error handling middleware"""

    def test_validation_error_response(self, client):
        """Test validation error response format"""
        # Send a GET request missing the required 'q' parameter
        response = client.get("/api/stocks/search")

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data  # FastAPI default validation error format

    def test_invalid_stock_symbol_response(self, client):
        """Test invalid stock symbol error response"""
        response = client.get("/api/stocks/INVALID123")

        assert response.status_code == 400
        data = response.json()
        assert data["success"] == False
        assert data["error"]["code"] in ("VALIDATION_ERROR", "INVALID_SYMBOL")

    def test_not_found_error_response(self, client):
        """Test not found error response"""
        response = client.get("/api/nonexistent")

        assert response.status_code == 404
        data = response.json()
        # Our custom error handler returns success=False
        assert data.get("success") == False or "detail" in data

    def test_error_includes_request_id(self, client):
        """Test that error responses include request ID"""
        response = client.get("/api/stocks/INVALID123")

        data = response.json()
        assert "request_id" in data.get("error", {})
