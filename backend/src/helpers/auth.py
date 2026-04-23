"""JWT + password utilities (spec §2.1).

- Passwords are hashed with bcrypt (cost configurable via ``BCRYPT_ROUNDS``).
- Access tokens are signed JWTs with ``sub``, ``role``, ``iat``, ``exp``, ``jti``.
- The caller is responsible for persisting ``jti`` into the blocklist on logout
  (see :mod:`services.auth_service`).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of ``plain``."""
    settings = get_settings()
    # passlib requires scheme-prefixed option keys on CryptContext.using().
    return _pwd_context.using(bcrypt__rounds=settings.BCRYPT_ROUNDS).hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time comparison of a plaintext password against a stored hash."""
    try:
        return _pwd_context.verify(plain, hashed)
    except ValueError:
        return False


def create_access_token(
    sub: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, str, datetime]:
    """Return ``(token, jti, expires_at)``. Caller stores jti for revocation."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    jti = uuid.uuid4().hex
    payload: dict[str, Any] = {
        "sub": sub,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": jti,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
    return token, jti, expire


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate ``token``. Raises :class:`JWTError` on any issue."""
    settings = get_settings()
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])


__all__ = [
    "JWTError",
    "create_access_token",
    "decode_access_token",
    "hash_password",
    "verify_password",
]
