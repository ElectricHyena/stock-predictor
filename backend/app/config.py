"""
Application Configuration
Settings and environment variables
"""

import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # API Configuration
    APP_NAME: str = "StockPredictor"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_V1_PREFIX: str = "/v1"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Database - using service name and port from environment
    # In Docker, services communicate via service name "postgres" on internal network
    # External connections use localhost with POSTGRES_PORT environment variable
    DATABASE_URL: str = ""
    DATABASE_ECHO: bool = True

    # Redis
    REDIS_URL: str = "redis://redis:6379"

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # News API
    NEWSAPI_KEY: str = ""

    # JWT/Auth
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Build DATABASE_URL from environment variables if not provided
        if not self.DATABASE_URL:
            postgres_user = os.getenv("POSTGRES_USER", "dev")
            postgres_password = os.getenv("POSTGRES_PASSWORD", "devpass")
            postgres_host = os.getenv("POSTGRES_HOST", "postgres")  # Docker service name
            postgres_port = os.getenv("POSTGRES_PORT", "5432")
            postgres_db = os.getenv("POSTGRES_DB", "stock_predictor")

            self.DATABASE_URL = (
                f"postgresql://{postgres_user}:{postgres_password}@"
                f"{postgres_host}:{postgres_port}/{postgres_db}"
            )


# Global settings instance
settings = Settings()
