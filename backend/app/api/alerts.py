"""
Alerts API Endpoints
Manage user alerts for stock price and prediction changes
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Alert, AlertTrigger, AlertType, AlertFrequency, AlertStatus, Stock
from app import schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])


# ============================================================================
# Alert CRUD Operations
# ============================================================================

@router.get("", response_model=List[schemas.AlertResponse])
async def get_user_alerts(
    user_id: int = Query(..., description="User ID"),
    status: Optional[str] = Query(None, description="Filter by status (active, triggered, disabled)"),
    db: Session = Depends(get_db)
):
    """Get all alerts for a user"""
    query = db.query(Alert).filter(Alert.user_id == user_id)

    if status:
        try:
            status_enum = AlertStatus(status)
            query = query.filter(Alert.status == status_enum)
        except ValueError:
            pass

    alerts = query.order_by(Alert.created_at.desc()).all()

    return [_alert_to_response(alert) for alert in alerts]


@router.post("", response_model=schemas.AlertResponse)
async def create_alert(
    request: schemas.AlertCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new alert"""
    # Validate stock exists
    stock = db.query(Stock).filter(Stock.ticker == request.ticker.upper()).first()
    if not stock:
        # Create stock with pending status
        stock = Stock(
            ticker=request.ticker.upper(),
            market="NYSE",
            company_name=request.ticker.upper(),
            analysis_status="PENDING"
        )
        db.add(stock)
        db.commit()
        db.refresh(stock)

    # Map alert type
    try:
        alert_type = AlertType(request.alert_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid alert type: {request.alert_type}")

    # Map frequency
    try:
        frequency = AlertFrequency(request.frequency) if request.frequency else AlertFrequency.REALTIME
    except ValueError:
        frequency = AlertFrequency.REALTIME

    alert = Alert(
        user_id=request.user_id,
        stock_id=stock.id,
        alert_type=alert_type,
        condition_value=request.condition_value,
        condition_operator=request.condition_operator or ">=",
        frequency=frequency,
        name=request.name,
        description=request.description,
        expires_at=request.expires_at,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    logger.info(f"Created alert {alert.id} for {stock.ticker}")

    return _alert_to_response(alert)


@router.get("/{alert_id}", response_model=schemas.AlertResponse)
async def get_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return _alert_to_response(alert)


@router.put("/{alert_id}", response_model=schemas.AlertResponse)
async def update_alert(
    alert_id: int,
    request: schemas.AlertUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if request.condition_value is not None:
        alert.condition_value = request.condition_value
    if request.condition_operator is not None:
        alert.condition_operator = request.condition_operator
    if request.frequency is not None:
        try:
            alert.frequency = AlertFrequency(request.frequency)
        except ValueError:
            pass
    if request.name is not None:
        alert.name = request.name
    if request.description is not None:
        alert.description = request.description
    if request.is_enabled is not None:
        alert.is_enabled = 1 if request.is_enabled else 0
        if request.is_enabled:
            alert.status = AlertStatus.ACTIVE
        else:
            alert.status = AlertStatus.DISABLED

    db.commit()
    db.refresh(alert)

    logger.info(f"Updated alert {alert_id}")

    return _alert_to_response(alert)


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Delete an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    db.delete(alert)
    db.commit()

    logger.info(f"Deleted alert {alert_id}")
    return {"message": "Alert deleted successfully"}


@router.post("/{alert_id}/enable", response_model=schemas.AlertResponse)
async def enable_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Enable an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_enabled = 1
    alert.status = AlertStatus.ACTIVE
    db.commit()
    db.refresh(alert)

    return _alert_to_response(alert)


@router.post("/{alert_id}/disable", response_model=schemas.AlertResponse)
async def disable_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Disable an alert without deleting"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_enabled = 0
    alert.status = AlertStatus.DISABLED
    db.commit()
    db.refresh(alert)

    return _alert_to_response(alert)


# ============================================================================
# Alert Triggers
# ============================================================================

@router.get("/{alert_id}/triggers", response_model=List[schemas.AlertTriggerResponse])
async def get_alert_triggers(
    alert_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get trigger history for an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    triggers = db.query(AlertTrigger).filter(
        AlertTrigger.alert_id == alert_id
    ).order_by(AlertTrigger.triggered_at.desc()).limit(limit).all()

    return [
        schemas.AlertTriggerResponse(
            id=t.id,
            alert_id=t.alert_id,
            triggered_value=t.triggered_value,
            message=t.message,
            is_read=t.is_read == 1,
            is_dismissed=t.is_dismissed == 1,
            triggered_at=t.triggered_at,
            read_at=t.read_at,
        )
        for t in triggers
    ]


@router.get("/triggers/unread", response_model=List[schemas.AlertTriggerResponse])
async def get_unread_triggers(
    user_id: int = Query(..., description="User ID"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get all unread alert triggers for a user"""
    triggers = db.query(AlertTrigger).join(Alert).filter(
        Alert.user_id == user_id,
        AlertTrigger.is_read == 0,
        AlertTrigger.is_dismissed == 0
    ).order_by(AlertTrigger.triggered_at.desc()).limit(limit).all()

    return [
        schemas.AlertTriggerResponse(
            id=t.id,
            alert_id=t.alert_id,
            triggered_value=t.triggered_value,
            message=t.message,
            is_read=t.is_read == 1,
            is_dismissed=t.is_dismissed == 1,
            triggered_at=t.triggered_at,
            read_at=t.read_at,
        )
        for t in triggers
    ]


@router.post("/triggers/{trigger_id}/read")
async def mark_trigger_read(
    trigger_id: int,
    db: Session = Depends(get_db)
):
    """Mark a trigger as read"""
    trigger = db.query(AlertTrigger).filter(AlertTrigger.id == trigger_id).first()

    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")

    trigger.is_read = 1
    trigger.read_at = datetime.utcnow()
    db.commit()

    return {"message": "Trigger marked as read"}


@router.post("/triggers/{trigger_id}/dismiss")
async def dismiss_trigger(
    trigger_id: int,
    db: Session = Depends(get_db)
):
    """Dismiss a trigger"""
    trigger = db.query(AlertTrigger).filter(AlertTrigger.id == trigger_id).first()

    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")

    trigger.is_dismissed = 1
    trigger.dismissed_at = datetime.utcnow()
    db.commit()

    return {"message": "Trigger dismissed"}


# ============================================================================
# Bulk Operations
# ============================================================================

@router.post("/bulk", response_model=List[schemas.AlertResponse])
async def create_bulk_alerts(
    request: schemas.BulkAlertCreateRequest,
    db: Session = Depends(get_db)
):
    """Create alerts for multiple stocks at once"""
    created_alerts = []

    for ticker in request.tickers:
        stock = db.query(Stock).filter(Stock.ticker == ticker.upper()).first()
        if not stock:
            stock = Stock(
                ticker=ticker.upper(),
                market="NYSE",
                company_name=ticker.upper(),
                analysis_status="PENDING"
            )
            db.add(stock)
            db.commit()
            db.refresh(stock)

        try:
            alert_type = AlertType(request.alert_type)
        except ValueError:
            continue

        try:
            frequency = AlertFrequency(request.frequency) if request.frequency else AlertFrequency.REALTIME
        except ValueError:
            frequency = AlertFrequency.REALTIME

        alert = Alert(
            user_id=request.user_id,
            stock_id=stock.id,
            alert_type=alert_type,
            condition_value=request.condition_value,
            condition_operator=request.condition_operator or ">=",
            frequency=frequency,
            name=f"{request.alert_type} alert for {ticker.upper()}",
        )
        db.add(alert)
        created_alerts.append(alert)

    db.commit()

    for alert in created_alerts:
        db.refresh(alert)

    logger.info(f"Created {len(created_alerts)} bulk alerts for user {request.user_id}")

    return [_alert_to_response(alert) for alert in created_alerts]


# ============================================================================
# Helper Functions
# ============================================================================

def _alert_to_response(alert: Alert) -> schemas.AlertResponse:
    """Convert Alert model to response schema"""
    return schemas.AlertResponse(
        id=alert.id,
        user_id=alert.user_id,
        stock_id=alert.stock_id,
        ticker=alert.stock.ticker,
        alert_type=alert.alert_type.value,
        condition_value=alert.condition_value,
        condition_operator=alert.condition_operator,
        frequency=alert.frequency.value,
        status=alert.status.value,
        is_enabled=alert.is_enabled == 1,
        name=alert.name,
        description=alert.description,
        trigger_count=len(alert.triggers),
        last_triggered_at=alert.last_triggered_at,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )
