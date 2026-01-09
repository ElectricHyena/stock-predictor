"""Pytest Configuration and Fixtures"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.config import settings


# Create test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override get_db dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    """Create test database tables and return session"""
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session):
    """Create test client with overridden dependencies"""
    app.dependency_overrides[get_db] = override_get_db

    # Clear cache before each test to ensure test isolation
    try:
        from app.cache import cache
        cache.clear()
    except Exception:
        pass  # Cache may not be available in all test environments

    with TestClient(app) as test_client:
        yield test_client

    # Clear cache after test as well
    try:
        from app.cache import cache
        cache.clear()
    except Exception:
        pass

    app.dependency_overrides.clear()


@pytest.fixture
def sample_stock_data():
    """Sample stock data for testing"""
    return {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "price": 150.0,
        "change": 2.5,
        "change_percent": 1.7,
        "market_cap": 2500000000000,
        "pe_ratio": 28.5,
        "eps": 5.25
    }


@pytest.fixture
def sample_prediction_data():
    """Sample prediction data for testing"""
    return {
        "symbol": "AAPL",
        "predicted_price": 155.0,
        "confidence": 0.85,
        "trend": "upward",
        "support_levels": [145.0, 140.0],
        "resistance_levels": [160.0, 165.0]
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User"
    }


@pytest.fixture
def sample_watchlist_data():
    """Sample watchlist data for testing"""
    return {
        "name": "My Watchlist",
        "description": "Test watchlist",
        "stocks": ["AAPL", "GOOGL", "MSFT"]
    }


# Pytest configuration and markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "e2e: end-to-end tests")
    config.addinivalue_line("markers", "slow: slow tests")
