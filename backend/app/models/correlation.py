"""Event-Price Correlation Model"""

from sqlalchemy import Column, Integer, Float, Date, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class EventPriceCorrelation(Base):
    """Historical correlations between events and price movements"""

    __tablename__ = "event_price_correlations"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    news_event_id = Column(Integer, ForeignKey("news_events.id"))

    # Event reference
    event_category = Column(String(50), nullable=False)
    event_date = Column(Date, nullable=False)

    # Price impact
    price_change_pct = Column(Float)  # Next day return %
    price_direction = Column(String(5))  # UP, DOWN, FLAT
    price_magnitude = Column(Float)  # Absolute change %

    # Timing analysis
    days_to_move = Column(Integer)  # How many days until move happened
    is_immediate = Column(Boolean)  # Within same day

    # Statistical metrics
    historical_win_rate = Column(Float)  # 0-1
    sample_size = Column(Integer)
    confidence_score = Column(Float)  # 0-1

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    stock = relationship("Stock", back_populates="correlations")

    def __repr__(self):
        return f"<EventPriceCorrelation(category={self.event_category}, win_rate={self.historical_win_rate})>"
