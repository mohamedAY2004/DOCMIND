"""Single entry point for recording admin-visible events (spec §10.5).

Every service that performs an admin-visible mutation calls
``ActivityLogger.record(...)`` exactly once per event.
"""
from __future__ import annotations

from typing import Any, Optional

from db.models import Activity, User
from repositories.activity_repository import ActivityRepository


class ActivityLogger:
    def __init__(self, activity_repo: ActivityRepository) -> None:
        self._repo = activity_repo

    async def record(
        self,
        *,
        action: str,
        actor: Optional[User] = None,
        subject_label: Optional[str] = None,
        meta: Optional[dict[str, Any]] = None,
    ) -> Activity:
        """Insert one activity row. Returns the created row."""
        activity = Activity(
            action=action,
            actor_user_id=actor.id if actor else None,
            subject_label=subject_label or (actor.name if actor else None),
            meta=meta,
        )
        return await self._repo.add(activity)
