"""StockPredictor Backend Application"""

__version__ = "0.1.0"

# Import Celery app so it can be discovered by Docker container
# This allows: celery -A app.tasks worker
from app.celery_config import celery_app  # noqa: F401
