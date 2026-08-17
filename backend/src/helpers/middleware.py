"""Request identity, CSRF, and Redis-backed pilot rate limits."""
from __future__ import annotations

import re
import secrets
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from helpers.auth import decode_access_token
from helpers.config import get_settings
from services.ephemeral_store import store_for

REQUEST_ID_HEADER = "X-Request-Id"
_SAFE_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")
_CHAT_TURN_PATHS = (
    re.compile(r"^/api/chat/(?:doc|tutor)/conversations/[^/]+/messages(?:/stream)?/?$"),
    re.compile(r"^/api/chat/doc/?$"),
    re.compile(r"^/api/chat/tutor/[^/]+/?$"),
    re.compile(r"^/api/subjects/[^/]+/test-bot(?:/stream)?/?$"),
)
_UPLOAD_PATHS = (
    re.compile(r"^/api/chat/doc/conversations/?$"),
    re.compile(r"^/api/chat/doc/conversations/[^/]+/files/?$"),
    re.compile(r"^/api/subjects/[^/]+/materials/?$"),
)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming if incoming and _SAFE_REQUEST_ID.fullmatch(incoming) else uuid.uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        if response.status_code >= 500:
            from services.telemetry_service import metrics
            metrics.increment("request_errors_total")
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        path = request.url.path
        method = request.method.upper()
        limit = window = None
        scope = ""
        identity = request.client.host if request.client else "unknown"
        settings = get_settings()
        if method == "POST" and (
            path.rstrip("/") in {
                "/api/auth/login",
                "/api/auth/sso/exchange",
                "/api/auth/sso/ticket",
            }
        ):
            limit = settings.AUTH_RATE_LIMIT
            window = settings.AUTH_RATE_WINDOW_SECONDS
            scope = "auth"
        elif method == "POST" and any(pattern.fullmatch(path) for pattern in _CHAT_TURN_PATHS):
            limit = settings.CHAT_RATE_LIMIT
            window = settings.CHAT_RATE_WINDOW_SECONDS
            scope = "chat"
            identity = _request_subject(request) or identity
        elif method == "POST" and any(pattern.fullmatch(path) for pattern in _UPLOAD_PATHS):
            limit = settings.UPLOAD_RATE_LIMIT
            window = settings.UPLOAD_RATE_WINDOW_SECONDS
            scope = "upload"
            identity = _request_subject(request) or identity
        if limit is not None and window is not None:
            bucket = int(time.time()) // window
            count = await store_for(request.app).increment(
                f"rate:{scope}:{identity}:{bucket}", window + 1
            )
            if count > limit:
                from services.telemetry_service import metrics
                metrics.increment("rate_limit_rejections_total")
                return JSONResponse(
                    status_code=429,
                    content={"code": "RATE_LIMITED", "message": "Too many requests. Please try again later."},
                    headers={"Retry-After": str(window)},
                )
        return await call_next(request)


class CSRFMiddleware(BaseHTTPMiddleware):
    _EXEMPT = {
        "/api/auth/login",
        "/api/auth/sso/start",
        "/api/auth/sso/ticket",
        "/api/auth/sso/exchange",
    }

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        if (
            request.method.upper() not in {"GET", "HEAD", "OPTIONS"}
            and request.url.path.rstrip("/") not in self._EXEMPT
            and (
                request.cookies.get("docmind_access")
                or request.cookies.get("docmind_refresh")
            )
            and not request.headers.get("Authorization")
        ):
            cookie = request.cookies.get("docmind_csrf", "")
            header = request.headers.get("X-CSRF-Token", "")
            if not cookie or not header or not secrets.compare_digest(cookie, header):
                return JSONResponse(
                    status_code=403,
                    content={"code": "FORBIDDEN", "message": "CSRF token is missing or invalid."},
                )
        return await call_next(request)


def _request_subject(request: Request) -> str | None:
    authorization = request.headers.get("Authorization", "")
    token = authorization[7:] if authorization.lower().startswith("bearer ") else request.cookies.get("docmind_access")
    if not token:
        return None
    try:
        return decode_access_token(token).get("sub")
    except Exception:  # noqa: BLE001
        return None
