"""News Event Model"""

from sqlalchemy import Column, Integer, String, DateTime, Date, Float, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class NewsEvent(Base):
    """News events and articles about stocks"""

    __tablename__ = "news_events"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)

    # News content
    headline = Column(String(500), nullable=False)
    content = Column(Text)

    # Event classification
    event_date = Column(Date, nullable=False, index=True)
    event_category = Column(String(50), nullable=False, index=True)  # earnings, policy, seasonal, technical, sector
    event_subcategory = Column(String(50))

    # Sentiment & source
    sentiment_score = Column(Float)  # -1.0 to 1.0
    sentiment_category = Column(String(20))  # POSITIVE, NEGATIVE, NEUTRAL
    source_name = Column(String(100))
    source_quality = Column(Float)  # 0.0 to 1.0

    # URLs & metadata
    original_url = Column(String(500))
    published_at = Column(DateTime)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    # Deduplication
    content_hash = Column(String(64), index=True)  # SHA256(headline + content)
    is_duplicate = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    stock = relationship("Stock", back_populates="news")

    def __repr__(self):
        return f"<NewsEvent(headline={self.headline[:50]}..., category={self.event_category})>"
