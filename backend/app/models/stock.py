"""Stock Model"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Stock(Base):
    """Stock master table"""

    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    company_name = Column(String(255))
    market = Column(String(10), nullable=False, index=True)  # NSE, BSE, NYSE
    sector = Column(String(100))
    industry = Column(String(100))
    website = Column(String(255))
    description = Column(Text)
    is_active = Column(Boolean, default=True, index=True)  # For enabling/disabling stock tracking

    # Data freshness tracking
    last_price_updated_at = Column(DateTime)
    last_news_updated_at = Column(DateTime)
    analysis_status = Column(String(20), default="PENDING")  # PENDING, PROCESSING, COMPLETED, FAILED

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (with cascade delete)
    prices = relationship("StockPrice", back_populates="stock", cascade="all, delete-orphan")
    news = relationship("NewsEvent", back_populates="stock", cascade="all, delete-orphan")
    correlations = relationship("EventPriceCorrelation", back_populates="stock", cascade="all, delete-orphan")
    watchlist_items = relationship("WatchlistItem", back_populates="stock", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="stock", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="stock", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Stock(ticker={self.ticker}, market={self.market})>"
