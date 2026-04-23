"""Data access for the singleton :class:`StudentAccessFlag`."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select

from db.models import StudentAccessFlag

from .base import BaseRepository


class SystemFlagRepository(BaseRepository[StudentAccessFlag]):
    model = StudentAccessFlag

    async def get_or_create(self) -> StudentAccessFlag:
        existing = await self.session.get(StudentAccessFlag, 1)
        if existing is not None:
            return existing
        flag = StudentAccessFlag(id=1, enabled=True, message="")
        self.session.add(flag)
        await self.session.flush()
        return flag

    async def update(
        self,
        *,
        enabled: bool,
        message: Optional[str],
    ) -> StudentAccessFlag:
        flag = await self.get_or_create()
        flag.enabled = enabled
        if message is not None:
            flag.message = message
        flag.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return flag
