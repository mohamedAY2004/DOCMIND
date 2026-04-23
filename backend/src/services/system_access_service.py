"""Global student-access flag management (spec §5 + §2.3)."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User
from repositories.activity_repository import ActivityRepository
from repositories.system_flag_repository import SystemFlagRepository
from schemas.system_access import StudentAccessResponse
from services.activity_logger import ActivityLogger


class SystemAccessService:
    def __init__(self, session: AsyncSession) -> None:
        self._flags = SystemFlagRepository(session)
        self._activity = ActivityLogger(ActivityRepository(session))

    async def get(self) -> StudentAccessResponse:
        flag = await self._flags.get_or_create()
        return StudentAccessResponse(
            enabled=flag.enabled,
            message=flag.message or "",
            updatedAt=flag.updated_at,
        )

    async def update(
        self,
        *,
        actor: User,
        enabled: bool,
        message: Optional[str],
    ) -> StudentAccessResponse:
        flag = await self._flags.update(enabled=enabled, message=message)
        action = "Student access enabled" if enabled else "Student access disabled"
        await self._activity.record(action=action, actor=actor)
        return StudentAccessResponse(
            enabled=flag.enabled,
            message=flag.message or "",
            updatedAt=flag.updated_at,
        )
