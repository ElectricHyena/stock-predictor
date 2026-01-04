"""API Routes and Routers"""

from fastapi import APIRouter

# API routers (imported from respective modules)
from app.api.stocks import router as stocks_router
from app.api.backtest import router as backtest_router
from app.api.router import api_router, configure_api_routes

__all__ = [
    "stocks_router",
    "backtest_router",
    "api_router",
    "configure_api_routes",
]
