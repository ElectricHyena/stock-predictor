"""
FastAPI Application Entry Point
Main application factory and middleware setup
"""

import logging
import time
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from contextlib import asynccontextmanager
from datetime import datetime

from app.config import settings
from app.database import Base, get_db
from app import schemas
from app.api.router import api_router, http_exception_handler, general_exception_handler
from app.metrics import metrics
from app.health import health_checker

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
    """Health check endpoint - basic liveness probe"""
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


@app.get("/health/live", tags=["health"])
async def liveness_probe():
    """Kubernetes liveness probe - is the app running?"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@app.get("/health/ready", tags=["health"])
async def readiness_probe():
    """Kubernetes readiness probe - is the app ready to serve traffic?"""
    health_status = await health_checker.check_all()
    if health_status["status"] == "healthy":
        return {"status": "ready", "checks": health_status["checks"]}
    return JSONResponse(
        status_code=503,
        content={"status": "not_ready", "checks": health_status["checks"]}
    )


@app.get("/metrics", tags=["monitoring"])
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(
        content=metrics.get_metrics_output(),
        media_type="text/plain; charset=utf-8"
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
    """Log all HTTP requests with metrics collection"""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    # Add request_id to request state for logging
    request.state.request_id = request_id

    logger.info(f"[{request_id}] {request.method} {request.url.path}")

    response = await call_next(request)

    duration = time.time() - start_time

    # Record metrics
    metrics.record_http_request(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
        duration=duration
    )

    logger.info(f"[{request_id}] {response.status_code} in {duration:.3f}s")

    # Add response headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration:.3f}s"

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
