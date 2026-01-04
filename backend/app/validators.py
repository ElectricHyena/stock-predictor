"""
Input Validation and Sanitization Utilities
"""
import re
from typing import Optional
from app.exceptions import (
    InvalidStockSymbolError,
    ValidationError,
    InsufficientDataError
)


class Validators:
    """Centralized validation utilities"""

    STOCK_SYMBOL_PATTERN = re.compile(r'^[A-Z]{1,5}$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    URL_PATTERN = re.compile(r'^https?://.+')

    # Valid stock exchanges
    VALID_EXCHANGES = [
        'NASDAQ', 'NYSE', 'AMEX', 'OTC', 'TSX',
        'LSE', 'EURONEXT', 'JSE', 'ASX', 'TSE'
    ]

    @staticmethod
    def validate_stock_symbol(symbol: str) -> str:
        """Validate stock symbol format"""
        if not symbol:
            raise InsufficientDataError("stock_symbol")

        symbol = symbol.upper().strip()

        if not Validators.STOCK_SYMBOL_PATTERN.match(symbol):
            raise InvalidStockSymbolError(symbol)

        return symbol

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format"""
        if not email:
            raise InsufficientDataError("email")

        email = email.strip().lower()

        if not Validators.EMAIL_PATTERN.match(email):
            raise ValidationError(
                f"Invalid email format: {email}",
                "INVALID_EMAIL"
            )

        return email

    @staticmethod
    def validate_url(url: str) -> str:
        """Validate URL format"""
        if not url:
            raise InsufficientDataError("url")

        url = url.strip()

        if not Validators.URL_PATTERN.match(url):
            raise ValidationError(
                f"Invalid URL format: {url}",
                "INVALID_URL"
            )

        return url

    @staticmethod
    def validate_numeric_range(
        value: float,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        field_name: str = "value"
    ) -> float:
        """Validate numeric value is within range"""
        if value is None:
            raise InsufficientDataError(field_name)

        try:
            num_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(
                f"{field_name} must be a number",
                f"INVALID_{field_name.upper()}"
            )

        if min_value is not None and num_value < min_value:
            raise ValidationError(
                f"{field_name} must be >= {min_value}",
                f"INVALID_{field_name.upper()}"
            )

        if max_value is not None and num_value > max_value:
            raise ValidationError(
                f"{field_name} must be <= {max_value}",
                f"INVALID_{field_name.upper()}"
            )

        return num_value

    @staticmethod
    def validate_string(
        value: str,
        field_name: str = "value",
        min_length: int = 1,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None
    ) -> str:
        """Validate string value"""
        if not value:
            raise InsufficientDataError(field_name)

        value = str(value).strip()

        if len(value) < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters",
                f"INVALID_{field_name.upper()}"
            )

        if max_length and len(value) > max_length:
            raise ValidationError(
                f"{field_name} must be no more than {max_length} characters",
                f"INVALID_{field_name.upper()}"
            )

        if pattern:
            regex = re.compile(pattern)
            if not regex.match(value):
                raise ValidationError(
                    f"{field_name} format is invalid",
                    f"INVALID_{field_name.upper()}"
                )

        return value

    @staticmethod
    def validate_enum(
        value: str,
        allowed_values: list,
        field_name: str = "value"
    ) -> str:
        """Validate value is in allowed list"""
        if value not in allowed_values:
            raise ValidationError(
                f"{field_name} must be one of: {', '.join(str(v) for v in allowed_values)}",
                f"INVALID_{field_name.upper()}"
            )

        return value

    @staticmethod
    def sanitize_input(value: str) -> str:
        """Sanitize input to prevent XSS"""
        if not isinstance(value, str):
            return value

        # Remove script tags and event handlers
        value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r'\s*on\w+\s*=', '', value, flags=re.IGNORECASE)
        value = re.sub(r'<\s*iframe[^>]*>.*?</\s*iframe\s*>', '', value, flags=re.IGNORECASE | re.DOTALL)

        return value

    @staticmethod
    def validate_integer(
        value,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        field_name: str = "value"
    ) -> int:
        """Validate integer value"""
        if value is None:
            raise InsufficientDataError(field_name)

        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(
                f"{field_name} must be an integer",
                f"INVALID_{field_name.upper()}"
            )

        if min_value is not None and int_value < min_value:
            raise ValidationError(
                f"{field_name} must be >= {min_value}",
                f"INVALID_{field_name.upper()}"
            )

        if max_value is not None and int_value > max_value:
            raise ValidationError(
                f"{field_name} must be <= {max_value}",
                f"INVALID_{field_name.upper()}"
            )

        return int_value
