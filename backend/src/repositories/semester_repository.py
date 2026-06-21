"""Data access for :class:`Semester`."""
from __future__ import annotations

from datetime import date
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

    async def upsert(
        self,
        sem_id: str,
        label: str,
        sort_order: int = 0,
        *,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Semester:
        existing = await self.session.get(Semester, sem_id)
        if existing is None:
            existing = Semester(
                id=sem_id,
                label=label,
                sort_order=sort_order,
                start_date=start_date,
                end_date=end_date,
            )
            self.session.add(existing)
        else:
            existing.label = label
            existing.sort_order = sort_order
            existing.start_date = start_date
            existing.end_date = end_date
        await self.session.flush()
        return existing

    async def update(
        self,
        semester: Semester,
        *,
        label: Optional[str] = None,
        sort_order: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Semester:
        """Apply a partial update to an already-loaded semester.

        ``None`` means "leave unchanged" — there is no separate sentinel for
        clearing a date back to NULL (admins set a window; they don't unset it),
        which keeps the PATCH semantics simple and matches the other admin
        update services.
        """
        if label is not None:
            semester.label = label
        if sort_order is not None:
            semester.sort_order = sort_order
        if start_date is not None:
            semester.start_date = start_date
        if end_date is not None:
            semester.end_date = end_date
        await self.session.flush()
        return semester
