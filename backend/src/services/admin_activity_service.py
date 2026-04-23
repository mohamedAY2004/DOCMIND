"""Admin activity feed service (spec §10.5)."""
from __future__ import annotations

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.activity_repository import ActivityRepository
from schemas.admin import ActivityResponse


class AdminActivityService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = ActivityRepository(session)

    async def list_recent(self, limit: int = 20) -> List[ActivityResponse]:
        rows = await self._repo.list_recent(limit=limit)
        return [
            ActivityResponse(
                id=row.id,
                action=row.action,
                user=row.subject_label,
                time=row.created_at,
            )
            for row in rows
        ]
