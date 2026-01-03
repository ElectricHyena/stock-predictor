"""
FastAPI Application Entry Point
Main application factory and middleware setup
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.database import Base
from app.api import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting StockPredictor API...")
    yield
    # Shutdown
    print("🛑 Shutting down StockPredictor API...")


# Create FastAPI application
app = FastAPI(
    title="StockPredictor API",
    description="Stock predictability analysis platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health Check Routes
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "stockpredictor-api"}


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API info"""
    return {
        "name": "StockPredictor API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


# Error Handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
