"""Alert Model - User alerts for stock price and prediction changes"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class AlertType(enum.Enum):
    """Types of alerts"""
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PRICE_CHANGE_PCT = "price_change_pct"
    PREDICTION_CHANGE = "prediction_change"
    VOLUME_SPIKE = "volume_spike"
    DIVIDEND = "dividend"
    PREDICTABILITY_CHANGE = "predictability_change"


class AlertFrequency(enum.Enum):
    """Alert notification frequency"""
    REALTIME = "realtime"
    DAILY_DIGEST = "daily_digest"
    WEEKLY_DIGEST = "weekly_digest"


class AlertStatus(enum.Enum):
    """Alert status"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    DISABLED = "disabled"
    EXPIRED = "expired"


class Alert(Base):
    """User alert configuration"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)

    # Alert configuration
    alert_type = Column(SQLEnum(AlertType), nullable=False, index=True)
    condition_value = Column(Float, nullable=False)  # Threshold value (price, %, etc.)
    condition_operator = Column(String(20), default=">=")  # >=, <=, >, <, ==
    frequency = Column(SQLEnum(AlertFrequency), default=AlertFrequency.REALTIME, nullable=False)

    # Status
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.ACTIVE, nullable=False, index=True)
    is_enabled = Column(Integer, default=1, nullable=False)

    # Metadata
    name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_triggered_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="alerts")
    stock = relationship("Stock", back_populates="alerts")
    triggers = relationship("AlertTrigger", back_populates="alert", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Alert(id={self.id}, type={self.alert_type}, stock_id={self.stock_id})>"


class AlertTrigger(Base):
    """Record of when an alert was triggered"""
    __tablename__ = "alert_triggers"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)

    # Trigger details
    triggered_value = Column(Float, nullable=False)  # The value that triggered the alert
    message = Column(Text, nullable=True)

    # Notification status
    is_read = Column(Integer, default=0, nullable=False)
    is_dismissed = Column(Integer, default=0, nullable=False)
    notified_via = Column(String(100), nullable=True)  # email, push, in_app

    # Timestamps
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    dismissed_at = Column(DateTime, nullable=True)

    # Relationships
    alert = relationship("Alert", back_populates="triggers")

    def __repr__(self):
        return f"<AlertTrigger(id={self.id}, alert_id={self.alert_id}, triggered_at={self.triggered_at})>"
