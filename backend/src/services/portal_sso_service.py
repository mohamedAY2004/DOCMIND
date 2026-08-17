"""State-bound, single-use portal bridge backed by Redis-compatible storage."""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from urllib.parse import urlencode

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from helpers.config import get_settings
from helpers.errors import APIError, ErrorCode
from repositories.user_repository import UserRepository
from services.ephemeral_store import EphemeralStore
from db.models import UserStatus


class PortalSSOService:
    def __init__(self, session: AsyncSession, store: EphemeralStore) -> None:
        self._users = UserRepository(session)
        self._store = store

    async def start(self) -> tuple[str, str]:
        state = secrets.token_urlsafe(32)
        await self._store.put(_state_key(state), "pending", 300)
        url = f"{get_settings().PORTAL_SSO_URL}?{urlencode({'state': state})}"
        return state, url

    async def create_ticket(
        self, *, state: str, user_id: str, issued_at: int, signature: str
    ) -> str:
        if abs(int(time.time()) - issued_at) > 60:
            raise APIError(ErrorCode.UNAUTHENTICATED, status.HTTP_401_UNAUTHORIZED, "Portal ticket expired.")
        message = f"{state}.{user_id}.{issued_at}".encode()
        expected = hmac.new(
            get_settings().PORTAL_SSO_SECRET.encode(), message, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise APIError(ErrorCode.UNAUTHENTICATED, status.HTTP_401_UNAUTHORIZED, "Invalid portal signature.")
        if await self._store.consume(_state_key(state)) is None:
            raise APIError(ErrorCode.UNAUTHENTICATED, status.HTTP_401_UNAUTHORIZED, "Invalid or replayed login state.")
        user = await self._users.get(user_id)
        if user is None or user.status == UserStatus.DISABLED:
            raise APIError(ErrorCode.UNAUTHENTICATED, status.HTTP_401_UNAUTHORIZED, "Portal user is not provisioned.")
        code = secrets.token_urlsafe(36)
        payload = json.dumps({"state": state, "userId": user_id}, separators=(",", ":"))
        await self._store.put(_code_key(code), payload, 60)
        return code

    async def exchange(self, *, state: str, code: str):
        raw = await self._store.consume(_code_key(code))
        if raw is None:
            raise APIError(ErrorCode.UNAUTHENTICATED, status.HTTP_401_UNAUTHORIZED, "Invalid or replayed exchange code.")
        payload = json.loads(raw)
        if not hmac.compare_digest(str(payload.get("state", "")), state):
            raise APIError(ErrorCode.UNAUTHENTICATED, status.HTTP_401_UNAUTHORIZED, "Login state mismatch.")
        user = await self._users.get(str(payload.get("userId", "")))
        if user is None or user.status == UserStatus.DISABLED:
            raise APIError(ErrorCode.UNAUTHENTICATED, status.HTTP_401_UNAUTHORIZED, "Portal user is not provisioned.")
        return user


def _state_key(state: str) -> str:
    return "sso:state:" + hashlib.sha256(state.encode()).hexdigest()


def _code_key(code: str) -> str:
    return "sso:code:" + hashlib.sha256(code.encode()).hexdigest()
