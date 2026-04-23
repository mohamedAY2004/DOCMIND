"""Public health-check endpoint (spec §3.5)."""
from __future__ import annotations

import time

from fastapi import APIRouter, Request

from helpers.config import get_settings

router = APIRouter(tags=["health"])

_STARTED_AT = time.time()


@router.get("/health")
async def health(_request: Request) -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "uptimeSec": int(time.time() - _STARTED_AT),
        "version": settings.APP_VERSION,
    }
