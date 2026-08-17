"""Issue and rotate secure browser cookie sessions."""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import RefreshSession, User, UserStatus
from helpers.auth import create_access_token
from helpers.config import get_settings
from helpers.errors import APIError, ErrorCode
from repositories.refresh_session_repository import RefreshSessionRepository
from repositories.user_repository import UserRepository


@dataclass(frozen=True)
class BrowserSession:
    access_token: str
    refresh_token: str
    csrf_token: str


class BrowserSessionService:
    def __init__(self, session: AsyncSession) -> None:
        self._refresh = RefreshSessionRepository(session)
        self._users = UserRepository(session)

    async def issue(self, user: User) -> BrowserSession:
        settings = get_settings()
        access, _, _ = create_access_token(
            user.id,
            user.role.value,
            expires_delta=timedelta(minutes=settings.ACCESS_COOKIE_MINUTES),
        )
        raw_refresh = secrets.token_urlsafe(48)
        await self._refresh.add(
            RefreshSession(
                user_id=user.id,
                token_hash=_hash(raw_refresh),
                expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_COOKIE_DAYS),
            )
        )
        return BrowserSession(access, raw_refresh, secrets.token_urlsafe(24))

    async def rotate(self, raw_refresh: str) -> tuple[User, BrowserSession]:
        record = await self._refresh.active_by_hash(_hash(raw_refresh))
        if record is None:
            raise APIError(ErrorCode.UNAUTHENTICATED, status.HTTP_401_UNAUTHORIZED, "Invalid refresh session.")
        user = await self._users.get(record.user_id)
        if user is None or user.status == UserStatus.DISABLED:
            await self._refresh.revoke(record)
            raise APIError(ErrorCode.UNAUTHENTICATED, status.HTTP_401_UNAUTHORIZED, "Account is no longer active.")
        replacement = await self.issue(user)
        new_record = await self._refresh.active_by_hash(_hash(replacement.refresh_token))
        await self._refresh.revoke(record, new_record)
        return user, replacement

    async def revoke(self, raw_refresh: str | None) -> None:
        if not raw_refresh:
            return
        record = await self._refresh.active_by_hash(_hash(raw_refresh))
        if record is not None:
            await self._refresh.revoke(record)


def set_browser_cookies(response: Response, session: BrowserSession) -> None:
    settings = get_settings()
    common = {
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "path": "/",
    }
    response.set_cookie(
        "docmind_access",
        session.access_token,
        httponly=True,
        max_age=settings.ACCESS_COOKIE_MINUTES * 60,
        **common,
    )
    response.set_cookie(
        "docmind_refresh",
        session.refresh_token,
        httponly=True,
        max_age=settings.REFRESH_COOKIE_DAYS * 86400,
        **common,
    )
    response.set_cookie(
        "docmind_csrf",
        session.csrf_token,
        httponly=False,
        max_age=settings.REFRESH_COOKIE_DAYS * 86400,
        **common,
    )


def clear_browser_cookies(response: Response) -> None:
    for name in ("docmind_access", "docmind_refresh", "docmind_csrf"):
        response.delete_cookie(name, path="/")


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
