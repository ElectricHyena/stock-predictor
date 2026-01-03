"""Event Category Model"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class EventCategory(Base):
    """Event categories for classification"""

    __tablename__ = "event_categories"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("news_events.id", ondelete="CASCADE"), nullable=False, index=True)

    # Category classification
    category = Column(String(50), nullable=False, index=True)
    confidence = Column(Float)  # 0-1 confidence score for category assignment

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<EventCategory(event_id={self.event_id}, category={self.category})>"
