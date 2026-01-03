"""Predictability Score Model"""

from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class PredictabilityScore(Base):
    """Predictability scores (computed daily)"""

    __tablename__ = "predictability_scores"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)

    # Score components (0-100)
    information_availability_score = Column(Integer)
    pattern_consistency_score = Column(Integer)
    timing_certainty_score = Column(Integer)
    direction_confidence_score = Column(Integer)

    # Final composite score
    overall_predictability_score = Column(Integer)

    # Current situation
    current_events = Column(JSON)  # Array of current events
    prediction_direction = Column(String(5))  # UP, DOWN
    prediction_magnitude_low = Column(Float)
    prediction_magnitude_high = Column(Float)

    # Metadata
    calculated_at = Column(DateTime)
    is_current = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PredictabilityScore(stock_id={self.stock_id}, score={self.overall_predictability_score})>"
