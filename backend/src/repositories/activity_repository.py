"""Data access for :class:`Activity`."""
from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select

from db.models import Activity

from .base import BaseRepository


class ActivityRepository(BaseRepository[Activity]):
    model = Activity

    async def list_recent(self, limit: int = 20) -> Sequence[Activity]:
        result = await self.session.execute(
            select(Activity).order_by(Activity.created_at.desc()).limit(limit)
        )
        return result.scalars().all()

    async def add(self, activity: Activity) -> Activity:
        self.session.add(activity)
        await self.session.flush()
        return activity
