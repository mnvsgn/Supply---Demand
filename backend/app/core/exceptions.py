"""
Core application exceptions and HTTP error handlers.
Re-exports and provides canonical application exceptions.
"""

from app.core.errors import (
    AppException,
    NotFoundException,
    ForbiddenException,
    ValidationException,
    DatasetUploadError,
    DatasetParsingError,
    DatasetValidationError,
    SchemaMappingError,
    ForecastError,
    InsufficientDataError,
    ModelNotEligibleError,
    SessionNotFoundError,
    SessionExpiredError,
    ErrorResponse,
    register_exception_handlers,
)

__all__ = [
    "AppException",
    "NotFoundException",
    "ForbiddenException",
    "ValidationException",
    "DatasetUploadError",
    "DatasetParsingError",
    "DatasetValidationError",
    "SchemaMappingError",
    "ForecastError",
    "InsufficientDataError",
    "ModelNotEligibleError",
    "SessionNotFoundError",
    "SessionExpiredError",
    "ErrorResponse",
    "register_exception_handlers",
]
