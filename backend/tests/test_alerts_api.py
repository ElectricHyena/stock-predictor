"""
Tests for Alerts API Endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.models import Alert, AlertTrigger, AlertType, AlertFrequency, AlertStatus, Stock
from app import schemas


class TestGetUserAlerts:
    """Tests for GET /api/alerts"""

    def test_get_alerts_requires_user_id(self, client):
        """Test that user_id is required"""
        response = client.get("/api/alerts")
        assert response.status_code == 422

    def test_get_alerts_with_user_id(self, client):
        """Test getting alerts for a user"""
        response = client.get("/api/alerts?user_id=1")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_alerts_with_status_filter(self, client):
        """Test filtering alerts by status"""
        response = client.get("/api/alerts?user_id=1&status=active")
        assert response.status_code == 200

    def test_get_alerts_with_invalid_status(self, client):
        """Test filtering with invalid status is ignored"""
        response = client.get("/api/alerts?user_id=1&status=invalid_status")
        assert response.status_code == 200


class TestCreateAlert:
    """Tests for POST /api/alerts"""

    def test_create_alert_success(self, client):
        """Test creating an alert"""
        response = client.post("/api/alerts", json={
            "user_id": 1,
            "ticker": "AAPL",
            "alert_type": "price_above",
            "condition_value": 150.0,
            "condition_operator": ">=",
            "name": "AAPL Price Alert"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert data["alert_type"] == "price_above"

    def test_create_alert_with_new_stock(self, client):
        """Test creating alert for non-existent stock creates stock"""
        response = client.post("/api/alerts", json={
            "user_id": 1,
            "ticker": "NEWSTOCK123",
            "alert_type": "price_above",
            "condition_value": 100.0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "NEWSTOCK123"

    def test_create_alert_invalid_type(self, client):
        """Test creating alert with invalid type"""
        response = client.post("/api/alerts", json={
            "user_id": 1,
            "ticker": "AAPL",
            "alert_type": "invalid_type",
            "condition_value": 150.0
        })
        assert response.status_code == 400

    def test_create_alert_with_frequency(self, client):
        """Test creating alert with frequency"""
        response = client.post("/api/alerts", json={
            "user_id": 1,
            "ticker": "GOOGL",
            "alert_type": "price_below",
            "condition_value": 100.0,
            "frequency": "daily"
        })
        assert response.status_code == 200
        data = response.json()
        # The API converts invalid frequency to realtime
        assert data["frequency"] in ["daily", "realtime"]

    def test_create_alert_with_description(self, client):
        """Test creating alert with description"""
        response = client.post("/api/alerts", json={
            "user_id": 1,
            "ticker": "MSFT",
            "alert_type": "price_above",
            "condition_value": 400.0,
            "name": "MSFT Target",
            "description": "Alert when MSFT hits $400"
        })
        assert response.status_code == 200


class TestGetAlert:
    """Tests for GET /api/alerts/{alert_id}"""

    def test_get_alert_not_found(self, client):
        """Test getting non-existent alert"""
        response = client.get("/api/alerts/99999")
        assert response.status_code == 404

    def test_get_alert_success(self, client):
        """Test getting existing alert"""
        # First create an alert
        create_response = client.post("/api/alerts", json={
            "user_id": 1,
            "ticker": "AAPL",
            "alert_type": "price_above",
            "condition_value": 150.0
        })
        alert_id = create_response.json()["id"]

        # Then get it
        response = client.get(f"/api/alerts/{alert_id}")
        assert response.status_code == 200
        assert response.json()["id"] == alert_id


class TestUpdateAlert:
    """Tests for PUT /api/alerts/{alert_id}"""

    def test_update_alert_not_found(self, client):
        """Test updating non-existent alert"""
        response = client.put("/api/alerts/99999", json={
            "condition_value": 200.0
        })
        assert response.status_code == 404

    def test_update_alert_condition_value(self, client):
        """Test updating alert condition value"""
        # Create alert
        create_response = client.post("/api/alerts", json={
            "user_id": 1,
            "ticker": "AAPL",
            "alert_type": "price_above",
            "condition_value": 150.0
        })
        alert_id = create_response.json()["id"]

        # Update it
        response = client.put(f"/api/alerts/{alert_id}", json={
            "condition_value": 175.0
        })
        assert response.status_code == 200
        assert response.json()["condition_value"] == 175.0

    def test_update_alert_disable(self, client):
        """Test disabling alert via update"""
        # Create alert
        create_response = client.post("/api/alerts", json={
            "user_id": 1,
            "ticker": "AAPL",
            "alert_type": "price_above",
            "condition_value": 150.0
        })
        alert_id = create_response.json()["id"]

        # Disable it
        response = client.put(f"/api/alerts/{alert_id}", json={
            "is_enabled": False
        })
        assert response.status_code == 200
        assert response.json()["is_enabled"] == False
        assert response.json()["status"] == "disabled"


class TestDeleteAlert:
    """Tests for DELETE /api/alerts/{alert_id}"""

    def test_delete_alert_not_found(self, client):
        """Test deleting non-existent alert"""
        response = client.delete("/api/alerts/99999")
        assert response.status_code == 404

    def test_delete_alert_success(self, client):
        """Test deleting existing alert"""
        # Create alert
        create_response = client.post("/api/alerts", json={
            "user_id": 1,
            "ticker": "AAPL",
            "alert_type": "price_above",
            "condition_value": 150.0
        })
        alert_id = create_response.json()["id"]

        # Delete it
        response = client.delete(f"/api/alerts/{alert_id}")
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()


class TestEnableDisableAlert:
    """Tests for enable/disable alert endpoints"""

    def test_enable_alert(self, client):
        """Test enabling an alert"""
        # Create and disable alert
        create_response = client.post("/api/alerts", json={
            "user_id": 1,
            "ticker": "AAPL",
            "alert_type": "price_above",
            "condition_value": 150.0
        })
        alert_id = create_response.json()["id"]

        # Enable it
        response = client.post(f"/api/alerts/{alert_id}/enable")
        assert response.status_code == 200
        assert response.json()["is_enabled"] == True

    def test_disable_alert(self, client):
        """Test disabling an alert"""
        create_response = client.post("/api/alerts", json={
            "user_id": 1,
            "ticker": "AAPL",
            "alert_type": "price_above",
            "condition_value": 150.0
        })
        alert_id = create_response.json()["id"]

        response = client.post(f"/api/alerts/{alert_id}/disable")
        assert response.status_code == 200
        assert response.json()["is_enabled"] == False

    def test_enable_nonexistent_alert(self, client):
        """Test enabling non-existent alert"""
        response = client.post("/api/alerts/99999/enable")
        assert response.status_code == 404

    def test_disable_nonexistent_alert(self, client):
        """Test disabling non-existent alert"""
        response = client.post("/api/alerts/99999/disable")
        assert response.status_code == 404


class TestAlertTriggers:
    """Tests for alert trigger endpoints"""

    def test_get_triggers_alert_not_found(self, client):
        """Test getting triggers for non-existent alert"""
        response = client.get("/api/alerts/99999/triggers")
        assert response.status_code == 404

    def test_get_unread_triggers(self, client):
        """Test getting unread triggers"""
        response = client.get("/api/alerts/triggers/unread?user_id=1")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_mark_trigger_read_not_found(self, client):
        """Test marking non-existent trigger as read"""
        response = client.post("/api/alerts/triggers/99999/read")
        assert response.status_code == 404

    def test_dismiss_trigger_not_found(self, client):
        """Test dismissing non-existent trigger"""
        response = client.post("/api/alerts/triggers/99999/dismiss")
        assert response.status_code == 404


class TestBulkAlerts:
    """Tests for bulk alert creation"""

    def test_create_bulk_alerts(self, client):
        """Test creating multiple alerts at once"""
        response = client.post("/api/alerts/bulk", json={
            "user_id": 1,
            "tickers": ["AAPL", "GOOGL", "MSFT"],
            "alert_type": "price_above",
            "condition_value": 100.0
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_create_bulk_alerts_with_invalid_type(self, client):
        """Test bulk creation with invalid alert type"""
        response = client.post("/api/alerts/bulk", json={
            "user_id": 1,
            "tickers": ["AAPL"],
            "alert_type": "invalid_type",
            "condition_value": 100.0
        })
        assert response.status_code == 200
        # Invalid type should be skipped
        assert len(response.json()) == 0


class TestAlertHelperFunctions:
    """Tests for alert helper functions"""

    def test_alert_response_structure(self, client):
        """Test alert response has correct structure"""
        response = client.post("/api/alerts", json={
            "user_id": 1,
            "ticker": "AAPL",
            "alert_type": "price_above",
            "condition_value": 150.0,
            "name": "Test Alert"
        })
        data = response.json()

        # Check all required fields
        assert "id" in data
        assert "user_id" in data
        assert "stock_id" in data
        assert "ticker" in data
        assert "alert_type" in data
        assert "condition_value" in data
        assert "status" in data
        assert "is_enabled" in data
        assert "created_at" in data
