from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from db.models import RefreshSession
from .base import BaseRepository


class RefreshSessionRepository(BaseRepository[RefreshSession]):
    model = RefreshSession

    async def add(self, record: RefreshSession) -> RefreshSession:
        self.session.add(record)
        await self.session.flush()
        return record

    async def active_by_hash(self, token_hash: str) -> RefreshSession | None:
        result = await self.session.execute(
            select(RefreshSession).where(
                RefreshSession.token_hash == token_hash,
                RefreshSession.revoked_at.is_(None),
                RefreshSession.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, record: RefreshSession, replacement: RefreshSession | None = None) -> None:
        record.revoked_at = datetime.now(timezone.utc)
        record.replaced_by_id = replacement.id if replacement else None
