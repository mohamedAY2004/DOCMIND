"""Data access for :class:`Semester`."""
from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select

from db.models import Semester

from .base import BaseRepository


class SemesterRepository(BaseRepository[Semester]):
    model = Semester

    async def list_all(self) -> Sequence[Semester]:
        result = await self.session.execute(
            select(Semester).order_by(Semester.sort_order.desc(), Semester.id.desc())
        )
        return result.scalars().all()

    async def upsert(self, sem_id: str, label: str, sort_order: int = 0) -> Semester:
        existing = await self.session.get(Semester, sem_id)
        if existing is None:
            existing = Semester(id=sem_id, label=label, sort_order=sort_order)
            self.session.add(existing)
        else:
            existing.label = label
            existing.sort_order = sort_order
        await self.session.flush()
        return existing
