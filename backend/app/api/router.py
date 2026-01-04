"""
API Router
Central router registration for all API endpoints
Includes error handling and middleware setup
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Union

from app import schemas
from app.api.stocks import router as stocks_router
from app.api.backtest import router as backtest_router
from app.api.watchlist import router as watchlist_router
from app.api.alerts import router as alerts_router

logger = logging.getLogger(__name__)

# Create main API router
api_router = APIRouter(prefix="/api", tags=["api"])

# Include sub-routers
api_router.include_router(stocks_router)
api_router.include_router(backtest_router)
api_router.include_router(watchlist_router)
api_router.include_router(alerts_router)


# ============================================================================
# Error Handlers
# ============================================================================

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    import uuid
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))

    # Determine error code from status code
    code_map = {
        400: "VALIDATION_ERROR",
        401: "AUTHENTICATION_REQUIRED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
    }
    error_code = code_map.get(exc.status_code, str(exc.status_code))

    logger.error(f"HTTP {exc.status_code}: {exc.detail} - {request.method} {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": exc.detail if isinstance(exc.detail, str) else "An error occurred",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id,
                "path": str(request.url.path),
            }
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    import uuid
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))

    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id,
                "path": str(request.url.path),
            }
        },
    )


# ============================================================================
# Request/Response Logging Middleware
# ============================================================================

async def logging_middleware(request: Request, call_next):
    """Log all requests and responses"""
    # Log request
    logger.info(f"{request.method} {request.url.path}")

    # Process request
    response = await call_next(request)

    # Log response
    logger.debug(f"Response: {response.status_code}")

    return response


# ============================================================================
# API Router Configuration
# ============================================================================

def configure_api_routes(app):
    """Configure all API routes and error handlers"""
    # Include main router
    app.include_router(api_router)

    # Add exception handlers
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Add middleware
    from fastapi.middleware import Middleware
    from fastapi.middleware.cors import CORSMiddleware
    from app.config import settings

    # CORS is already configured in main.py, but we can add request logging here
    logger.info("API routes configured successfully")
