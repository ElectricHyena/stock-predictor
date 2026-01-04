"""
Watchlist API Endpoints
Manage user watchlists and tracked stocks
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Watchlist, WatchlistItem, Stock, User
from app import schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


# ============================================================================
# Watchlist CRUD Operations
# ============================================================================

@router.get("", response_model=List[schemas.WatchlistResponse])
async def get_user_watchlists(
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get all watchlists for a user"""
    watchlists = db.query(Watchlist).filter(Watchlist.user_id == user_id).all()

    result = []
    for wl in watchlists:
        # Get stock details for each item
        items = []
        for item in wl.items:
            stock = item.stock
            items.append(schemas.WatchlistItemResponse(
                id=item.id,
                stock_id=item.stock_id,
                ticker=stock.ticker,
                company_name=stock.company_name,
                notes=item.notes,
                tags=item.tags.split(",") if item.tags else [],
                added_at=item.added_at,
            ))

        result.append(schemas.WatchlistResponse(
            id=wl.id,
            name=wl.name,
            description=wl.description,
            is_default=wl.is_default == 1,
            item_count=len(wl.items),
            items=items,
            created_at=wl.created_at,
            updated_at=wl.updated_at,
        ))

    return result


@router.post("", response_model=schemas.WatchlistResponse)
async def create_watchlist(
    request: schemas.WatchlistCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new watchlist"""
    # Check if watchlist with same name exists for user
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == request.user_id,
        Watchlist.name == request.name
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Watchlist with this name already exists")

    watchlist = Watchlist(
        user_id=request.user_id,
        name=request.name,
        description=request.description,
    )
    db.add(watchlist)
    db.commit()
    db.refresh(watchlist)

    logger.info(f"Created watchlist '{request.name}' for user {request.user_id}")

    return schemas.WatchlistResponse(
        id=watchlist.id,
        name=watchlist.name,
        description=watchlist.description,
        is_default=watchlist.is_default == 1,
        item_count=0,
        items=[],
        created_at=watchlist.created_at,
        updated_at=watchlist.updated_at,
    )


@router.get("/{watchlist_id}", response_model=schemas.WatchlistResponse)
async def get_watchlist(
    watchlist_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific watchlist with all items"""
    watchlist = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    items = []
    for item in watchlist.items:
        stock = item.stock
        items.append(schemas.WatchlistItemResponse(
            id=item.id,
            stock_id=item.stock_id,
            ticker=stock.ticker,
            company_name=stock.company_name,
            notes=item.notes,
            tags=item.tags.split(",") if item.tags else [],
            added_at=item.added_at,
        ))

    return schemas.WatchlistResponse(
        id=watchlist.id,
        name=watchlist.name,
        description=watchlist.description,
        is_default=watchlist.is_default == 1,
        item_count=len(watchlist.items),
        items=items,
        created_at=watchlist.created_at,
        updated_at=watchlist.updated_at,
    )


@router.put("/{watchlist_id}", response_model=schemas.WatchlistResponse)
async def update_watchlist(
    watchlist_id: int,
    request: schemas.WatchlistUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update a watchlist"""
    watchlist = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    if request.name:
        watchlist.name = request.name
    if request.description is not None:
        watchlist.description = request.description

    db.commit()
    db.refresh(watchlist)

    items = []
    for item in watchlist.items:
        stock = item.stock
        items.append(schemas.WatchlistItemResponse(
            id=item.id,
            stock_id=item.stock_id,
            ticker=stock.ticker,
            company_name=stock.company_name,
            notes=item.notes,
            tags=item.tags.split(",") if item.tags else [],
            added_at=item.added_at,
        ))

    return schemas.WatchlistResponse(
        id=watchlist.id,
        name=watchlist.name,
        description=watchlist.description,
        is_default=watchlist.is_default == 1,
        item_count=len(watchlist.items),
        items=items,
        created_at=watchlist.created_at,
        updated_at=watchlist.updated_at,
    )


@router.delete("/{watchlist_id}")
async def delete_watchlist(
    watchlist_id: int,
    db: Session = Depends(get_db)
):
    """Delete a watchlist"""
    watchlist = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    if watchlist.is_default == 1:
        raise HTTPException(status_code=400, detail="Cannot delete default watchlist")

    db.delete(watchlist)
    db.commit()

    logger.info(f"Deleted watchlist {watchlist_id}")
    return {"message": "Watchlist deleted successfully"}


# ============================================================================
# Watchlist Item Operations
# ============================================================================

@router.post("/{watchlist_id}/stocks", response_model=schemas.WatchlistItemResponse)
async def add_stock_to_watchlist(
    watchlist_id: int,
    request: schemas.WatchlistAddStockRequest,
    db: Session = Depends(get_db)
):
    """Add a stock to a watchlist"""
    watchlist = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    # Find or create stock
    stock = db.query(Stock).filter(Stock.ticker == request.ticker.upper()).first()
    if not stock:
        # Create new stock with pending status
        stock = Stock(
            ticker=request.ticker.upper(),
            market=request.market or "NYSE",
            company_name=request.ticker.upper(),
            analysis_status="PENDING"
        )
        db.add(stock)
        db.commit()
        db.refresh(stock)

    # Check if stock already in watchlist
    existing = db.query(WatchlistItem).filter(
        WatchlistItem.watchlist_id == watchlist_id,
        WatchlistItem.stock_id == stock.id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Stock already in watchlist")

    item = WatchlistItem(
        watchlist_id=watchlist_id,
        stock_id=stock.id,
        notes=request.notes,
        tags=",".join(request.tags) if request.tags else None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    logger.info(f"Added {stock.ticker} to watchlist {watchlist_id}")

    return schemas.WatchlistItemResponse(
        id=item.id,
        stock_id=item.stock_id,
        ticker=stock.ticker,
        company_name=stock.company_name,
        notes=item.notes,
        tags=item.tags.split(",") if item.tags else [],
        added_at=item.added_at,
    )


@router.put("/{watchlist_id}/stocks/{stock_id}", response_model=schemas.WatchlistItemResponse)
async def update_watchlist_item(
    watchlist_id: int,
    stock_id: int,
    request: schemas.WatchlistUpdateItemRequest,
    db: Session = Depends(get_db)
):
    """Update notes/tags for a stock in watchlist"""
    item = db.query(WatchlistItem).filter(
        WatchlistItem.watchlist_id == watchlist_id,
        WatchlistItem.stock_id == stock_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Stock not found in watchlist")

    if request.notes is not None:
        item.notes = request.notes
    if request.tags is not None:
        item.tags = ",".join(request.tags)

    db.commit()
    db.refresh(item)

    stock = item.stock
    return schemas.WatchlistItemResponse(
        id=item.id,
        stock_id=item.stock_id,
        ticker=stock.ticker,
        company_name=stock.company_name,
        notes=item.notes,
        tags=item.tags.split(",") if item.tags else [],
        added_at=item.added_at,
    )


@router.delete("/{watchlist_id}/stocks/{stock_id}")
async def remove_stock_from_watchlist(
    watchlist_id: int,
    stock_id: int,
    db: Session = Depends(get_db)
):
    """Remove a stock from a watchlist"""
    item = db.query(WatchlistItem).filter(
        WatchlistItem.watchlist_id == watchlist_id,
        WatchlistItem.stock_id == stock_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Stock not found in watchlist")

    db.delete(item)
    db.commit()

    logger.info(f"Removed stock {stock_id} from watchlist {watchlist_id}")
    return {"message": "Stock removed from watchlist"}


# ============================================================================
# Default Watchlist Creation
# ============================================================================

@router.post("/default", response_model=schemas.WatchlistResponse)
async def create_default_watchlist(
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Create default 'Portfolio' watchlist for a user"""
    # Check if default already exists
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == user_id,
        Watchlist.is_default == 1
    ).first()

    if existing:
        return schemas.WatchlistResponse(
            id=existing.id,
            name=existing.name,
            description=existing.description,
            is_default=True,
            item_count=len(existing.items),
            items=[],
            created_at=existing.created_at,
            updated_at=existing.updated_at,
        )

    watchlist = Watchlist(
        user_id=user_id,
        name="Portfolio",
        description="Your default portfolio watchlist",
        is_default=1,
    )
    db.add(watchlist)
    db.commit()
    db.refresh(watchlist)

    logger.info(f"Created default watchlist for user {user_id}")

    return schemas.WatchlistResponse(
        id=watchlist.id,
        name=watchlist.name,
        description=watchlist.description,
        is_default=True,
        item_count=0,
        items=[],
        created_at=watchlist.created_at,
        updated_at=watchlist.updated_at,
    )
