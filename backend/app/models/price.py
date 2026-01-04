"""Stock Price Model"""

from sqlalchemy import Column, Integer, Float, DateTime, Date, Boolean, String, ForeignKey, BigInteger, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class StockPrice(Base):
    """Historical stock price data (OHLCV)"""

    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # OHLCV
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(BigInteger)
    adjusted_close = Column(Float)

    # Calculated fields
    daily_return_pct = Column(Float)  # (close - prev_close) / prev_close
    price_range = Column(Float)  # (high - low) / open

    # Data quality flags
    is_valid = Column(Boolean, default=True)
    data_source = Column(String(50))  # yahoo_finance, etc

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    stock = relationship("Stock", back_populates="prices")

    __table_args__ = (
        # Composite unique constraint to prevent duplicate dates for same stock
        UniqueConstraint('stock_id', 'date', name='uq_stock_date'),
    )

    def __repr__(self):
        return f"<StockPrice(stock_id={self.stock_id}, date={self.date}, close={self.close_price})>"
