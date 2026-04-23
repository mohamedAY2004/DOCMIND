"""Authentication business logic (spec §4 + §2.3)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, UserRole, UserStatus
from helpers.auth import (
    create_access_token,
    decode_access_token,
    verify_password,
)
from helpers.errors import APIError, ErrorCode
from repositories.system_flag_repository import SystemFlagRepository
from repositories.token_blocklist_repository import TokenBlocklistRepository
from repositories.user_repository import UserRepository
from schemas.auth import LoginResponse, MeResponse, UserSummary

_REDIRECT_BY_ROLE: dict[UserRole, str] = {
    UserRole.STUDENT: "/home",
    UserRole.INSTRUCTOR: "/instructor",
    UserRole.ADMIN: "/admin",
}


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._flags = SystemFlagRepository(session)
        self._blocklist = TokenBlocklistRepository(session)

    async def login(self, username: str, password: str) -> LoginResponse:
        """Validate credentials and return a signed JWT + user summary."""
        user = await self._users.get_by_username(username)
        # Generic error — never leak whether the account exists (spec §4.1).
        if user is None or not verify_password(password, user.password_hash):
            raise APIError(
                ErrorCode.UNAUTHENTICATED,
                status.HTTP_401_UNAUTHORIZED,
                "Invalid username or password.",
            )
        if user.status == UserStatus.DISABLED:
            raise APIError(
                ErrorCode.UNAUTHENTICATED,
                status.HTTP_401_UNAUTHORIZED,
                "Invalid username or password.",
            )

        # Student-access gate — only affects students (spec §2.3).
        if user.role == UserRole.STUDENT:
            flag = await self._flags.get_or_create()
            if not flag.enabled:
                raise APIError(
                    ErrorCode.STUDENT_ACCESS_DISABLED,
                    status.HTTP_403_FORBIDDEN,
                    flag.message or "Student access is currently disabled.",
                )

        token, _jti, _exp = create_access_token(sub=user.id, role=user.role.value)
        await self._users.touch_last_active(user.id)

        return LoginResponse(
            token=token,
            user=UserSummary(
                id=user.id,
                username=user.username,
                name=user.name,
                role=user.role.value,
            ),
            redirect=_REDIRECT_BY_ROLE[user.role],
            welcomeMessage=f"Welcome back, {user.name}!",
        )

    async def logout(self, jti: str) -> None:
        """Revoke the token's ``jti``. Idempotent."""
        try:
            payload = _safe_decode(jti)
        except Exception:
            payload = None
        expires_at = _expiry_from_payload(payload)
        await self._blocklist.revoke(jti, expires_at)

    async def me(self, user: User) -> MeResponse:
        return MeResponse(
            user=UserSummary(
                id=user.id,
                username=user.username,
                name=user.name,
                role=user.role.value,
            )
        )


def _safe_decode(token_or_jti: str) -> Optional[dict]:
    try:
        return decode_access_token(token_or_jti)
    except Exception:
        return None


def _expiry_from_payload(payload: Optional[dict]) -> datetime:
    if payload and "exp" in payload:
        try:
            return datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc)
        except Exception:  # noqa: BLE001
            pass
    # Fallback: blocklist for 24h.
    return datetime.now(timezone.utc).replace(microsecond=0)
