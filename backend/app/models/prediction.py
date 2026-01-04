"""Prediction Model - Stock price predictions"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class PredictionDirection(enum.Enum):
    """Prediction direction"""
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


class PredictionTiming(enum.Enum):
    """Prediction timing horizon"""
    SAME_DAY = "same_day"
    NEXT_DAY = "next_day"
    LAGGED = "lagged"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Prediction(Base):
    """Stock price prediction record"""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)

    # Prediction details
    direction = Column(SQLEnum(PredictionDirection), nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    timing = Column(SQLEnum(PredictionTiming), nullable=False)

    # Expected move
    expected_move_min = Column(Float, nullable=True)  # Minimum expected % move
    expected_move_max = Column(Float, nullable=True)  # Maximum expected % move

    # Historical basis
    historical_win_rate = Column(Float, nullable=True)  # 0.0 to 1.0
    sample_size = Column(Integer, nullable=True)  # Number of historical occurrences

    # Reasoning
    reasoning = Column(Text, nullable=True)
    based_on_events = Column(Text, nullable=True)  # JSON array of event IDs

    # Prediction date
    prediction_date = Column(DateTime, nullable=False, index=True)
    target_date = Column(DateTime, nullable=True)  # When the prediction is for

    # Outcome tracking (filled in after target date)
    actual_move = Column(Float, nullable=True)  # Actual % move
    was_correct = Column(Integer, nullable=True)  # 1 = correct, 0 = incorrect

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    stock = relationship("Stock", back_populates="predictions")

    def __repr__(self):
        return f"<Prediction(id={self.id}, stock_id={self.stock_id}, direction={self.direction})>"
