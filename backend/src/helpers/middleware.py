"""HTTP middlewares (spec §2.4 requires X-Request-Id on every response)."""
from __future__ import annotations

import re
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-Id"

# Only echo a client-supplied request id when it is a short, safe token.
# Anything else (control chars, newlines, oversized values) is replaced with a
# freshly minted id to avoid log-forging / header-injection.
_SAFE_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Echo a *validated* client-supplied ``X-Request-Id`` or mint a new UUID4."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request_id = (
            incoming
            if incoming and _SAFE_REQUEST_ID.fullmatch(incoming)
            else uuid.uuid4().hex
        )
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Stub. Real rate limiting should live at the gateway / reverse proxy.

    Kept here so the import surface of ``helpers.middleware`` is stable, and
    so that spec §2.6 defaults (chat 60/min/user, uploads 20/hour/user, etc.)
    can be enforced later without changing the app bootstrap.
    """

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        return await call_next(request)
