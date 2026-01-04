"""
Global Error Handling Middleware for FastAPI
"""
import logging
import uuid
from datetime import datetime
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from app.exceptions import StockPredictorException

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware"""

    async def dispatch(self, request: Request, call_next):
        """Handle all requests and catch exceptions"""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            return response

        except StockPredictorException as exc:
            return await self._handle_app_exception(request, exc, request_id)
        except RequestValidationError as exc:
            return await self._handle_validation_error(request, exc, request_id)
        except Exception as exc:
            return await self._handle_generic_exception(request, exc, request_id)

    async def _handle_app_exception(self, request: Request, error: StockPredictorException, request_id: str):
        """Handle application-specific exceptions"""
        logger.error(
            f"Application error: {error.code}",
            extra={
                "request_id": request_id,
                "error_code": error.code,
                "status_code": error.status_code,
                "message": error.message,
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown"
            }
        )

        return JSONResponse(
            status_code=error.status_code,
            content={
                "success": False,
                "error": {
                    "code": error.code,
                    "message": error.message,
                    "timestamp": error.timestamp,
                    "request_id": request_id
                }
            }
        )

    async def _handle_validation_error(self, request: Request, error: RequestValidationError, request_id: str):
        """Handle Pydantic validation errors"""
        logger.warning(
            "Validation error",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "errors": error.errors()
            }
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": request_id,
                    "details": [
                        {
                            "field": ".".join(str(x) for x in err["loc"]),
                            "message": err["msg"],
                            "type": err["type"]
                        }
                        for err in error.errors()
                    ]
                }
            }
        )

    async def _handle_generic_exception(self, request: Request, error: Exception, request_id: str):
        """Handle unexpected exceptions"""
        logger.error(
            "Unexpected error",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "error_type": type(error).__name__,
                "error_message": str(error)
            },
            exc_info=True
        )

        # Don't expose internal error details to client
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred",
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": request_id
                }
            }
        )
