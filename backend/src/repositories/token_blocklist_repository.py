"""Data access for the revoked-token blocklist."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select

from db.models import TokenBlocklist

from .base import BaseRepository


class TokenBlocklistRepository(BaseRepository[TokenBlocklist]):
    model = TokenBlocklist

    async def is_revoked(self, jti: str) -> bool:
        row = await self.session.execute(
            select(TokenBlocklist.jti).where(TokenBlocklist.jti == jti)
        )
        return row.scalar_one_or_none() is not None

    async def revoke(self, jti: str, expires_at: datetime) -> None:
        existing = await self.session.get(TokenBlocklist, jti)
        if existing is not None:
            return
        self.session.add(TokenBlocklist(jti=jti, expires_at=expires_at))
        await self.session.flush()

    async def purge_expired(self, now: datetime) -> int:
        result = await self.session.execute(
            delete(TokenBlocklist).where(TokenBlocklist.expires_at < now)
        )
        return result.rowcount or 0
