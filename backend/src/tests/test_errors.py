"""Unit tests for the error envelope + APIError serialization.

These tests do not require a database — they exercise the handlers directly.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

from helpers.errors import APIError, ErrorCode, install_exception_handlers


def test_error_codes_are_strings() -> None:
    """Every ErrorCode value must be a string; the frontend relies on this."""
    for code in ErrorCode:
        assert isinstance(code.value, str)
        assert code.value.isupper()


def test_apierror_round_trip() -> None:
    err = APIError(
        ErrorCode.FORBIDDEN, 403, "Nope", details={"missingScope": "admin"}
    )
    assert err.code is ErrorCode.FORBIDDEN
    assert err.http_status == 403
    assert err.message == "Nope"
    assert err.details == {"missingScope": "admin"}


def test_install_exception_handlers_is_idempotent() -> None:
    """Calling the installer twice should not raise — the docstring promises so."""
    from fastapi import FastAPI

    app = FastAPI()
    install_exception_handlers(app)
    install_exception_handlers(app)
