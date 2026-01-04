"""
FastAPI Application Entry Point
Main application factory and middleware setup
"""

import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime

from app.config import settings
from app.database import Base
from app import schemas
from app.api.router import api_router, http_exception_handler, general_exception_handler

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting StockPredictor API...")
    yield
    # Shutdown
    logger.info("Shutting down StockPredictor API...")


# Create FastAPI application
app = FastAPI(
    title="StockPredictor API",
    description="Stock predictability analysis platform with event-driven price prediction",
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health Check Routes
# ============================================================================

@app.get("/health", tags=["health"], response_model=schemas.HealthResponse)
async def health_check():
    """Health check endpoint"""
    return schemas.HealthResponse(
        status="ok",
        service="stockpredictor-api",
        timestamp=datetime.utcnow(),
        version="0.2.0",
        dependencies={
            "database": "postgresql",
            "cache": "redis",
            "task_queue": "celery"
        }
    )


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API info"""
    return {
        "name": "StockPredictor API",
        "version": "0.2.0",
        "description": "Stock predictability analysis and price prediction platform",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "health": "/health",
            "api": "/api",
        },
        "api_version": "v1"
    }


# ============================================================================
# API Routes
# ============================================================================

# Include main API router
app.include_router(api_router)


# ============================================================================
# Error Handlers
# ============================================================================

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# ============================================================================
# Request Logging Middleware
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    logger.debug(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.debug(f"Response: {response.status_code}")
    return response


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
        access_log=True,
    )
