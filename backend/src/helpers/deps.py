"""FastAPI dependencies for auth, RBAC, DB sessions, and the student-access gate."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import AsyncIterator, Callable

from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, UserRole, UserStatus
from helpers.auth import decode_access_token
from helpers.config import get_settings
from helpers.errors import APIError, ErrorCode
from repositories.system_flag_repository import SystemFlagRepository
from repositories.token_blocklist_repository import TokenBlocklistRepository
from repositories.user_repository import UserRepository

# ``auto_error=False`` lets us keep the existing error envelope (APIError +
# ErrorCode.UNAUTHENTICATED) instead of FastAPI's default 403 response, while
# still registering the scheme in the OpenAPI doc so Swagger UI shows the
# "Authorize" button and attaches the Bearer token on every request.
bearer_scheme = HTTPBearer(auto_error=False)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped SQLAlchemy session. Commits on success."""
    factory = request.app.state.session_maker
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def _parse_bearer(credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials is None:
        raise APIError(
            ErrorCode.UNAUTHENTICATED,
            status.HTTP_401_UNAUTHORIZED,
            "Missing Authorization header.",
        )
    if credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise APIError(
            ErrorCode.UNAUTHENTICATED,
            status.HTTP_401_UNAUTHORIZED,
            "Invalid Authorization header format.",
        )
    return credentials.credentials


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Resolve the authenticated user from a Bearer JWT.

    Raises ``401 UNAUTHENTICATED`` on any failure. Never returns ``403`` for
    auth problems — spec §2.1 is explicit about this.
    """
    token = _parse_bearer(credentials)
    try:
        payload = decode_access_token(token)
    except JWTError as e:
        raise APIError(
            ErrorCode.UNAUTHENTICATED,
            status.HTTP_401_UNAUTHORIZED,
            "Invalid or expired token.",
        ) from e

    jti = payload.get("jti")
    sub = payload.get("sub")
    if not sub or not jti:
        raise APIError(
            ErrorCode.UNAUTHENTICATED,
            status.HTTP_401_UNAUTHORIZED,
            "Malformed token.",
        )

    blocklist_repo = TokenBlocklistRepository(session)
    if await blocklist_repo.is_revoked(jti):
        raise APIError(
            ErrorCode.UNAUTHENTICATED,
            status.HTTP_401_UNAUTHORIZED,
            "Token has been revoked.",
        )

    user = await UserRepository(session).get(sub)
    if user is None or user.status == UserStatus.DISABLED:
        raise APIError(
            ErrorCode.UNAUTHENTICATED,
            status.HTTP_401_UNAUTHORIZED,
            "Account is no longer active.",
        )

    # Spec §9: keep last_active fresh, but throttle the write so plain GETs don't
    # each incur a user-row UPDATE (and a rollback hazard on later read errors).
    throttle = get_settings().LAST_ACTIVE_THROTTLE_SECONDS
    now = datetime.now(timezone.utc)
    last_active = user.last_active
    if last_active is not None and last_active.tzinfo is None:
        last_active = last_active.replace(tzinfo=timezone.utc)
    if last_active is None or (now - last_active).total_seconds() >= throttle:
        await UserRepository(session).touch_last_active(user.id)
    return user


def require_role(*roles: UserRole) -> Callable[[User], User]:
    """Dependency factory enforcing that the caller has one of ``roles``."""

    def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise APIError(
                ErrorCode.FORBIDDEN,
                status.HTTP_403_FORBIDDEN,
                "You do not have permission to perform this action.",
            )
        return user

    return _check


async def require_student_access(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Block student callers when the global student-access flag is off.

    Instructors and admins pass through unconditionally. Students receive the
    exact ``403 STUDENT_ACCESS_DISABLED`` body mandated by spec §2.3.
    """
    if user.role != UserRole.STUDENT:
        return user
    flag = await SystemFlagRepository(session).get_or_create()
    if not flag.enabled:
        raise APIError(
            ErrorCode.STUDENT_ACCESS_DISABLED,
            status.HTTP_403_FORBIDDEN,
            flag.message or "Student access is currently disabled.",
        )
    return user


async def ensure_subject_access(
    session: AsyncSession, user: User, subject_id: str
) -> None:
    """Per-subject enrollment gate.

    - Admins always pass.
    - Instructors must be on the subject's instructor roster.
    - Students must be on the subject's student roster.
    Raises 404 if the subject does not exist, 403 otherwise.
    """
    from repositories.subject_repository import SubjectRepository

    subjects = SubjectRepository(session)
    if await subjects.get(subject_id) is None:
        raise APIError(
            ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Subject not found."
        )
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.INSTRUCTOR:
        if not await subjects.is_instructor_of(subject_id, user.id):
            raise APIError(
                ErrorCode.FORBIDDEN,
                status.HTTP_403_FORBIDDEN,
                "You are not assigned to this subject.",
            )
        return
    # student
    if not await subjects.is_student_of(subject_id, user.id):
        raise APIError(
            ErrorCode.FORBIDDEN,
            status.HTTP_403_FORBIDDEN,
            "You are not enrolled in this subject.",
        )


async def require_subject_access(
    subject_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_student_access),
) -> User:
    """FastAPI dep enforcing per-subject access for the path param ``subject_id``."""
    await ensure_subject_access(session, user, subject_id)
    return user


# Convenience role-specific dependencies (kept here so routes import a single name).
def require_admin() -> Callable[[User], User]:
    return require_role(UserRole.ADMIN)


def require_instructor_or_admin() -> Callable[[User], User]:
    return require_role(UserRole.INSTRUCTOR, UserRole.ADMIN)


def require_student() -> Callable[[User], User]:
    return require_role(UserRole.STUDENT)


def get_logout_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> tuple[str, datetime]:
    """Return ``(jti, expires_at)`` from the caller's token for /auth/logout.

    The blocklist row should live exactly until the token would have expired, so
    we derive ``expires_at`` from the token's own ``exp`` claim here (the route
    only ever had the ``jti`` before, which made the expiry meaningless)."""
    token = _parse_bearer(credentials)
    try:
        payload = decode_access_token(token)
    except JWTError as e:
        raise APIError(
            ErrorCode.UNAUTHENTICATED,
            status.HTTP_401_UNAUTHORIZED,
            "Invalid or expired token.",
        ) from e
    jti = payload.get("jti")
    if not jti:
        raise APIError(
            ErrorCode.UNAUTHENTICATED,
            status.HTTP_401_UNAUTHORIZED,
            "Malformed token.",
        )
    exp = payload.get("exp")
    if exp is not None:
        expires_at = datetime.fromtimestamp(int(exp), tz=timezone.utc)
    else:
        # No exp claim (shouldn't happen for our tokens) — fall back to the
        # configured token lifetime so the row still gets purged eventually.
        expires_at = now_plus_token_lifetime()
    return jti, expires_at


def now_plus_token_lifetime() -> datetime:
    settings = get_settings()
    from datetime import timedelta

    return datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
