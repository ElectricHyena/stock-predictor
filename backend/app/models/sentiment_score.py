"""Sentiment Score Model"""

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from datetime import datetime

from app.database import Base


class SentimentScore(Base):
    """Sentiment analysis scores for events"""

    __tablename__ = "sentiment_scores"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("news_events.id", ondelete="CASCADE"), nullable=False, index=True)

    # Sentiment scoring
    sentiment_score = Column(Float, nullable=False)  # -1.0 to 1.0

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SentimentScore(event_id={self.event_id}, score={self.sentiment_score})>"
