from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.logging import logger


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[Any] = None
    code: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        code: str = "BAD_REQUEST",
        detail: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.detail = detail


class NotFoundException(AppException):
    def __init__(
        self,
        message: str = "Resource not found",
        detail: Optional[Any] = None,
        code: str = "NOT_FOUND",
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            code=code,
            detail=detail,
        )


class ForbiddenException(AppException):
    def __init__(
        self,
        message: str = "Access forbidden",
        detail: Optional[Any] = None,
        code: str = "FORBIDDEN",
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            code=code,
            detail=detail,
        )


class SessionExpiredException(AppException):
    def __init__(
        self,
        message: str = "Session has expired or does not exist",
        detail: Optional[Any] = None,
        code: str = "SESSION_EXPIRED",
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            code=code,
            detail=detail,
        )


class ValidationException(AppException):
    def __init__(
        self,
        message: str = "Validation error",
        detail: Optional[Any] = None,
        code: str = "VALIDATION_ERROR",
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=code,
            detail=detail,
        )


class UnsupportedMediaTypeException(AppException):
    def __init__(
        self,
        message: str = "Unsupported file type",
        detail: Optional[Any] = None,
        code: str = "UNSUPPORTED_MEDIA_TYPE",
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            code=code,
            detail=detail,
        )


class PayloadTooLargeException(AppException):
    def __init__(
        self,
        message: str = "File size exceeds allowed limit",
        detail: Optional[Any] = None,
        code: str = "PAYLOAD_TOO_LARGE",
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code=code,
            detail=detail,
        )


class FileValidationException(AppException):
    def __init__(
        self,
        message: str = "Invalid file content or structure",
        detail: Optional[Any] = None,
        code: str = "INVALID_FILE_STRUCTURE",
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        super().__init__(
            message=message,
            status_code=status_code,
            code=code,
            detail=detail,
        )


def register_error_handlers(app: FastAPI) -> None:
    """Registers global exception handlers for consistent API error responses."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(f"AppException on {request.url.path}: {exc.message} ({exc.code})")
        payload = ErrorResponse(
            error=exc.message,
            detail=exc.detail,
            code=exc.code,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=payload.model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
        payload = ErrorResponse(
            error="Request validation failed",
            detail=exc.errors(),
            code="UNPROCESSABLE_ENTITY",
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=payload.model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        logger.warning(f"HTTPException on {request.url.path}: {exc.detail} (HTTP {exc.status_code})")
        payload = ErrorResponse(
            error=str(exc.detail),
            detail=None,
            code=f"HTTP_{exc.status_code}",
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=payload.model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled exception on {request.url.path}: {str(exc)}")
        payload = ErrorResponse(
            error="An internal server error occurred",
            detail=str(exc) if request.app.debug else None,
            code="INTERNAL_SERVER_ERROR",
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=payload.model_dump(),
        )
