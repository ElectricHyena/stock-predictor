"""
Database Configuration
SQLAlchemy setup and session management with connection pooling
"""

from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator
import os

from app.config import settings

# Connection pooling configuration
# pool_size: number of connections to keep in the pool
# max_overflow: maximum overflow size (connections beyond pool_size)
# pool_recycle: recycle connections after this many seconds (helps with connection timeout issues)
# pool_pre_ping: test connection before using it (helps with connection issues)

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
    # Connection pooling configuration
    poolclass=pool.QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,  # Recycle connections every hour
    pool_pre_ping=True,  # Test connections before using
    connect_args={
        "connect_timeout": 10,
    },
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

# Base class for models
Base = declarative_base()

# Import all models so they're registered with Base
# This MUST happen after Base is defined but before migrations
from app.models import (  # noqa: F401, E402
    User,
    Stock,
    StockPrice,
    NewsEvent,
    EventPriceCorrelation,
    PredictabilityScore,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
