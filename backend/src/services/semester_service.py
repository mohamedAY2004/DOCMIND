"""Semester business logic (spec §6.6).

Semesters were previously read straight from the repository by the router. This
service centralises that read (so the derived lifecycle state lives in one place)
and adds the admin create/update writes.
"""
from __future__ import annotations

from typing import List

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Semester, SemesterState, User, derive_semester_state
from helpers.errors import APIError, ErrorCode
from repositories.activity_repository import ActivityRepository
from repositories.semester_repository import SemesterRepository
from schemas.semester import (
    CreateSemesterRequest,
    SemesterResponse,
    UpdateSemesterRequest,
)
from services.activity_logger import ActivityLogger


class SemesterService:
    def __init__(self, session: AsyncSession) -> None:
        self._semesters = SemesterRepository(session)
        self._activity = ActivityLogger(ActivityRepository(session))

    def _to_response(self, semester: Semester) -> SemesterResponse:
        state = derive_semester_state(semester.start_date, semester.end_date)
        return SemesterResponse(
            id=semester.id,
            label=semester.label,
            sortOrder=semester.sort_order,
            startDate=semester.start_date,
            endDate=semester.end_date,
            state=state.value,
            isCurrent=state == SemesterState.ACTIVE,
        )

    async def list_all(self) -> List[SemesterResponse]:
        return [self._to_response(s) for s in await self._semesters.list_all()]

    async def get_current(self) -> List[SemesterResponse]:
        """Every semester whose derived state is ``active`` (overlap allowed)."""
        return [r for r in await self.list_all() if r.isCurrent]

    async def get_or_404(self, semester_id: str) -> Semester:
        semester = await self._semesters.get(semester_id)
        if semester is None:
            raise APIError(
                ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Semester not found."
            )
        return semester

    async def create(
        self, actor: User, body: CreateSemesterRequest
    ) -> SemesterResponse:
        if await self._semesters.get(body.id) is not None:
            raise APIError(
                ErrorCode.CONFLICT,
                status.HTTP_409_CONFLICT,
                f"Semester '{body.id}' already exists.",
            )
        self._validate_window(body.startDate, body.endDate)
        semester = await self._semesters.upsert(
            body.id,
            body.label,
            body.sortOrder,
            start_date=body.startDate,
            end_date=body.endDate,
        )
        await self._activity.record(
            action="Semester created", actor=actor, subject_label=semester.label
        )
        return self._to_response(semester)

    async def update(
        self, actor: User, semester_id: str, body: UpdateSemesterRequest
    ) -> SemesterResponse:
        semester = await self.get_or_404(semester_id)
        # Validate against the *effective* window (incoming value or current).
        self._validate_window(
            body.startDate if body.startDate is not None else semester.start_date,
            body.endDate if body.endDate is not None else semester.end_date,
        )
        semester = await self._semesters.update(
            semester,
            label=body.label,
            sort_order=body.sortOrder,
            start_date=body.startDate,
            end_date=body.endDate,
        )
        await self._activity.record(
            action="Semester updated", actor=actor, subject_label=semester.label
        )
        return self._to_response(semester)

    async def delete(self, actor: User, semester_id: str) -> None:
        """Remove a semester. Subjects that reference it are unassigned, not
        deleted — the ``Subject.semester_id`` FK is ``ON DELETE SET NULL``."""
        semester = await self.get_or_404(semester_id)
        label = semester.label
        await self._activity.record(
            action="Semester deleted", actor=actor, subject_label=label
        )
        await self._semesters.delete(semester)

    @staticmethod
    def _validate_window(start, end) -> None:
        if start is not None and end is not None and end < start:
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                status.HTTP_400_BAD_REQUEST,
                "endDate must be on or after startDate.",
            )
