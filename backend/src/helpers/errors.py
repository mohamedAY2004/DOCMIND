"""Standardized error envelope and global exception handlers (spec §2.4).

Every error response body is:

    {
        "code":    "<ERROR_CODE>",
        "message": "<human readable>",
        "details": {optional per-field errors}
    }

and carries an ``X-Request-Id`` header (populated by the middleware).
"""
from __future__ import annotations

import enum
import logging
from typing import Any, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("docmind.errors")


class ErrorCode(str, enum.Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN = "FORBIDDEN"
    STUDENT_ACCESS_DISABLED = "STUDENT_ACCESS_DISABLED"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    UNPROCESSABLE = "UNPROCESSABLE"
    FILE_UNSAFE = "FILE_UNSAFE"
    FILE_ENCRYPTED = "FILE_ENCRYPTED"
    FILE_LIMIT = "FILE_LIMIT"
    FILES_NOT_READY = "FILES_NOT_READY"
    SUBJECT_NOT_READY = "SUBJECT_NOT_READY"
    CANNOT_DISABLE_SELF = "CANNOT_DISABLE_SELF"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class APIError(Exception):
    """Typed application error. Services raise this; the handler serializes it."""

    def __init__(
        self,
        code: ErrorCode,
        http_status: int,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.http_status = http_status
        self.message = message
        self.details = details


def _envelope(
    code: ErrorCode, message: str, details: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    body: dict[str, Any] = {"code": code.value, "message": message}
    if details is not None:
        body["details"] = details
    return body


def install_exception_handlers(app: FastAPI) -> None:
    """Register every exception handler in one shot."""

    @app.exception_handler(APIError)
    async def _api_error_handler(_request: Request, exc: APIError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content=_envelope(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_envelope(
                ErrorCode.VALIDATION_ERROR,
                "Request body failed validation.",
                details={"errors": exc.errors()},
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code = _http_status_to_code(exc.status_code)
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(code, message),
        )

    @app.exception_handler(Exception)
    async def _unhandled_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope(
                ErrorCode.INTERNAL_ERROR, "An unexpected error occurred."
            ),
        )


def _http_status_to_code(http_status: int) -> ErrorCode:
    """Best-effort mapping from raw HTTP code to a spec-conformant error code."""
    return {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.UNAUTHENTICATED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONFLICT,
        413: ErrorCode.FILE_TOO_LARGE,
        415: ErrorCode.UNSUPPORTED_MEDIA_TYPE,
        422: ErrorCode.UNPROCESSABLE,
        429: ErrorCode.RATE_LIMITED,
    }.get(http_status, ErrorCode.INTERNAL_ERROR)
