"""
Tests for Watchlist API Endpoints
"""
import pytest
from datetime import datetime


class TestGetUserWatchlists:
    """Tests for GET /api/watchlists"""

    def test_get_watchlists_requires_user_id(self, client):
        """Test that user_id is required"""
        response = client.get("/api/watchlists")
        assert response.status_code == 422

    def test_get_watchlists_with_user_id(self, client):
        """Test getting watchlists for a user"""
        response = client.get("/api/watchlists?user_id=1")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_watchlists_empty_user(self, client):
        """Test getting watchlists for user with no watchlists"""
        response = client.get("/api/watchlists?user_id=99999")
        assert response.status_code == 200
        assert response.json() == []


class TestCreateWatchlist:
    """Tests for POST /api/watchlists"""

    def test_create_watchlist_success(self, client):
        """Test creating a watchlist"""
        response = client.post("/api/watchlists", json={
            "user_id": 1,
            "name": "Tech Stocks",
            "description": "My favorite tech stocks"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Tech Stocks"
        assert data["description"] == "My favorite tech stocks"
        assert data["item_count"] == 0

    def test_create_watchlist_duplicate_name(self, client):
        """Test creating watchlist with duplicate name"""
        # Create first watchlist
        client.post("/api/watchlists", json={
            "user_id": 2,
            "name": "Unique Watchlist",
            "description": "First one"
        })

        # Try to create duplicate
        response = client.post("/api/watchlists", json={
            "user_id": 2,
            "name": "Unique Watchlist",
            "description": "Duplicate"
        })
        assert response.status_code == 400
        # Response might have detail or message field
        resp_data = response.json()
        error_message = resp_data.get("detail") or resp_data.get("message") or str(resp_data)
        assert "already exists" in error_message.lower()

    def test_create_watchlist_without_description(self, client):
        """Test creating watchlist without description"""
        response = client.post("/api/watchlists", json={
            "user_id": 1,
            "name": "Simple Watchlist"
        })
        assert response.status_code == 200


class TestGetWatchlist:
    """Tests for GET /api/watchlists/{watchlist_id}"""

    def test_get_watchlist_not_found(self, client):
        """Test getting non-existent watchlist"""
        response = client.get("/api/watchlists/99999")
        assert response.status_code == 404

    def test_get_watchlist_success(self, client):
        """Test getting existing watchlist"""
        # Create watchlist
        create_response = client.post("/api/watchlists", json={
            "user_id": 1,
            "name": "Test Watchlist"
        })
        watchlist_id = create_response.json()["id"]

        # Get it
        response = client.get(f"/api/watchlists/{watchlist_id}")
        assert response.status_code == 200
        assert response.json()["id"] == watchlist_id


class TestUpdateWatchlist:
    """Tests for PUT /api/watchlists/{watchlist_id}"""

    def test_update_watchlist_not_found(self, client):
        """Test updating non-existent watchlist"""
        response = client.put("/api/watchlists/99999", json={
            "name": "New Name"
        })
        assert response.status_code == 404

    def test_update_watchlist_name(self, client):
        """Test updating watchlist name"""
        # Create watchlist
        create_response = client.post("/api/watchlists", json={
            "user_id": 1,
            "name": "Old Name"
        })
        watchlist_id = create_response.json()["id"]

        # Update name
        response = client.put(f"/api/watchlists/{watchlist_id}", json={
            "name": "New Name"
        })
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    def test_update_watchlist_description(self, client):
        """Test updating watchlist description"""
        # Create watchlist
        create_response = client.post("/api/watchlists", json={
            "user_id": 1,
            "name": "Test WL"
        })
        watchlist_id = create_response.json()["id"]

        # Update description
        response = client.put(f"/api/watchlists/{watchlist_id}", json={
            "description": "Updated description"
        })
        assert response.status_code == 200
        assert response.json()["description"] == "Updated description"


class TestDeleteWatchlist:
    """Tests for DELETE /api/watchlists/{watchlist_id}"""

    def test_delete_watchlist_not_found(self, client):
        """Test deleting non-existent watchlist"""
        response = client.delete("/api/watchlists/99999")
        assert response.status_code == 404

    def test_delete_watchlist_success(self, client):
        """Test deleting existing watchlist"""
        # Create watchlist
        create_response = client.post("/api/watchlists", json={
            "user_id": 1,
            "name": "To Delete"
        })
        watchlist_id = create_response.json()["id"]

        # Delete it
        response = client.delete(f"/api/watchlists/{watchlist_id}")
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()


class TestAddStockToWatchlist:
    """Tests for POST /api/watchlists/{watchlist_id}/stocks"""

    def test_add_stock_watchlist_not_found(self, client):
        """Test adding stock to non-existent watchlist"""
        response = client.post("/api/watchlists/99999/stocks", json={
            "ticker": "AAPL"
        })
        assert response.status_code == 404

    def test_add_stock_success(self, client):
        """Test adding stock to watchlist"""
        # Create watchlist
        create_response = client.post("/api/watchlists", json={
            "user_id": 1,
            "name": "Stock Watchlist"
        })
        watchlist_id = create_response.json()["id"]

        # Add stock
        response = client.post(f"/api/watchlists/{watchlist_id}/stocks", json={
            "ticker": "AAPL",
            "notes": "Buy the dip"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert data["notes"] == "Buy the dip"

    def test_add_stock_with_tags(self, client):
        """Test adding stock with tags"""
        # Create watchlist
        create_response = client.post("/api/watchlists", json={
            "user_id": 1,
            "name": "Tagged Watchlist"
        })
        watchlist_id = create_response.json()["id"]

        # Add stock with tags
        response = client.post(f"/api/watchlists/{watchlist_id}/stocks", json={
            "ticker": "GOOGL",
            "tags": ["tech", "growth"]
        })
        assert response.status_code == 200
        assert "tech" in response.json()["tags"]

    def test_add_duplicate_stock(self, client):
        """Test adding duplicate stock to watchlist"""
        # Create watchlist
        create_response = client.post("/api/watchlists", json={
            "user_id": 1,
            "name": "Duplicate Test"
        })
        watchlist_id = create_response.json()["id"]

        # Add stock first time
        client.post(f"/api/watchlists/{watchlist_id}/stocks", json={
            "ticker": "MSFT"
        })

        # Try to add again
        response = client.post(f"/api/watchlists/{watchlist_id}/stocks", json={
            "ticker": "MSFT"
        })
        assert response.status_code == 400
        resp_data = response.json()
        error_message = resp_data.get("detail") or resp_data.get("message") or str(resp_data)
        assert "already" in error_message.lower()

    def test_add_new_stock_creates_stock(self, client):
        """Test adding non-existent stock creates it"""
        # Create watchlist
        create_response = client.post("/api/watchlists", json={
            "user_id": 1,
            "name": "New Stock Test"
        })
        watchlist_id = create_response.json()["id"]

        # Add stock that doesn't exist
        response = client.post(f"/api/watchlists/{watchlist_id}/stocks", json={
            "ticker": "NEWSTK999",
            "market": "NASDAQ"
        })
        assert response.status_code == 200
        assert response.json()["ticker"] == "NEWSTK999"


class TestUpdateWatchlistItem:
    """Tests for PUT /api/watchlists/{watchlist_id}/stocks/{stock_id}"""

    def test_update_item_not_found(self, client):
        """Test updating non-existent item"""
        response = client.put("/api/watchlists/99999/stocks/99999", json={
            "notes": "Updated"
        })
        assert response.status_code == 404

    def test_update_item_notes(self, client):
        """Test updating item notes"""
        # Create watchlist and add stock
        create_response = client.post("/api/watchlists", json={
            "user_id": 1,
            "name": "Update Notes Test"
        })
        watchlist_id = create_response.json()["id"]

        add_response = client.post(f"/api/watchlists/{watchlist_id}/stocks", json={
            "ticker": "AAPL"
        })
        stock_id = add_response.json()["stock_id"]

        # Update notes
        response = client.put(f"/api/watchlists/{watchlist_id}/stocks/{stock_id}", json={
            "notes": "New notes"
        })
        assert response.status_code == 200
        assert response.json()["notes"] == "New notes"

    def test_update_item_tags(self, client):
        """Test updating item tags"""
        # Create watchlist and add stock
        create_response = client.post("/api/watchlists", json={
            "user_id": 1,
            "name": "Update Tags Test"
        })
        watchlist_id = create_response.json()["id"]

        add_response = client.post(f"/api/watchlists/{watchlist_id}/stocks", json={
            "ticker": "GOOGL"
        })
        stock_id = add_response.json()["stock_id"]

        # Update tags
        response = client.put(f"/api/watchlists/{watchlist_id}/stocks/{stock_id}", json={
            "tags": ["new_tag", "updated"]
        })
        assert response.status_code == 200
        assert "new_tag" in response.json()["tags"]


class TestRemoveStockFromWatchlist:
    """Tests for DELETE /api/watchlists/{watchlist_id}/stocks/{stock_id}"""

    def test_remove_stock_not_found(self, client):
        """Test removing non-existent stock"""
        response = client.delete("/api/watchlists/99999/stocks/99999")
        assert response.status_code == 404

    def test_remove_stock_success(self, client):
        """Test removing stock from watchlist"""
        # Create watchlist and add stock
        create_response = client.post("/api/watchlists", json={
            "user_id": 1,
            "name": "Remove Stock Test"
        })
        watchlist_id = create_response.json()["id"]

        add_response = client.post(f"/api/watchlists/{watchlist_id}/stocks", json={
            "ticker": "AAPL"
        })
        stock_id = add_response.json()["stock_id"]

        # Remove it
        response = client.delete(f"/api/watchlists/{watchlist_id}/stocks/{stock_id}")
        assert response.status_code == 200
        assert "removed" in response.json()["message"].lower()


class TestDefaultWatchlist:
    """Tests for POST /api/watchlists/default"""

    def test_create_default_watchlist(self, client):
        """Test creating default watchlist"""
        response = client.post("/api/watchlists/default?user_id=100")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Portfolio"
        assert data["is_default"] == True

    def test_create_default_already_exists(self, client):
        """Test creating default when one already exists"""
        # Create first default
        client.post("/api/watchlists/default?user_id=101")

        # Try again - should return existing
        response = client.post("/api/watchlists/default?user_id=101")
        assert response.status_code == 200
        assert response.json()["is_default"] == True


class TestDeleteDefaultWatchlist:
    """Test that default watchlist cannot be deleted"""

    def test_cannot_delete_default_watchlist(self, client):
        """Test that default watchlist cannot be deleted"""
        # Create default watchlist
        create_response = client.post("/api/watchlists/default?user_id=102")
        watchlist_id = create_response.json()["id"]

        # Try to delete it
        response = client.delete(f"/api/watchlists/{watchlist_id}")
        assert response.status_code == 400
        resp_data = response.json()
        error_message = resp_data.get("detail") or resp_data.get("message") or str(resp_data)
        assert "default" in error_message.lower() or "cannot delete" in error_message.lower()


class TestWatchlistResponseStructure:
    """Tests for response structure validation"""

    def test_watchlist_response_structure(self, client):
        """Test watchlist response has correct structure"""
        response = client.post("/api/watchlists", json={
            "user_id": 1,
            "name": "Structure Test",
            "description": "Test description"
        })
        data = response.json()

        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "is_default" in data
        assert "item_count" in data
        assert "items" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_watchlist_item_response_structure(self, client):
        """Test watchlist item response has correct structure"""
        # Create watchlist
        create_response = client.post("/api/watchlists", json={
            "user_id": 1,
            "name": "Item Structure Test"
        })
        watchlist_id = create_response.json()["id"]

        # Add stock
        response = client.post(f"/api/watchlists/{watchlist_id}/stocks", json={
            "ticker": "AAPL"
        })
        data = response.json()

        assert "id" in data
        assert "stock_id" in data
        assert "ticker" in data
        assert "company_name" in data
        assert "notes" in data
        assert "tags" in data
        assert "added_at" in data
