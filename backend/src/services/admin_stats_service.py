"""Admin analytics + subject-stats service (spec §10.3, §10.6)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    Conversation,
    ConversationKind,
    Feedback,
    FeedbackValue,
    Material,
    MaterialStatus,
    Message,
    MessageRole,
    Subject,
)
from helpers.pagination import Page, PaginationParams
from repositories.subject_stats_repository import SubjectStatsRepository
from repositories.message_repository import MessageRepository
from repositories.subject_repository import SubjectRepository
from schemas.admin import DailyUsageResponse, SubjectStatsResponse


class AdminStatsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._messages = MessageRepository(session)
        self._subjects = SubjectRepository(session)

    async def list_subject_stats(
        self, params: PaginationParams
    ) -> Page[SubjectStatsResponse]:
        subjects, total = await self._subjects.list_paginated(
            search=params.search, offset=params.offset, limit=params.page_size)
        totals = await SubjectStatsRepository(self._session).for_subjects([s.id for s in subjects])
        items = []
        for subject in subjects:
            counts = totals[subject.id]
            material_status = ("empty" if not counts["materials"] else "processed"
                               if counts["materials"] == counts["processed"] else "indexing"
                               if not counts["processed"] else "mixed")
            items.append(SubjectStatsResponse(
                id=subject.id, title=subject.title, semester=subject.semester_id,
                pdfCount=counts["materials"], materialStatus=material_status,
                interactions=counts["interactions"], aiResponses=counts["responses"],
                thumbsUp=counts["up"], thumbsDown=counts["down"],
                instructorIds=counts["instructors"], superInstructorId=counts["super_id"]))
        return Page.build(items=items, total=total, params=params)

    async def daily_usage(
        self,
        days: int = 14,
        *,
        subject_id: Optional[str] = None,
        semester_id: Optional[str] = None,
        instructor_id: Optional[str] = None,
    ) -> List[DailyUsageResponse]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        rows = await self._messages.daily_rollup(
            since,
            subject_id=subject_id,
            semester_id=semester_id,
            instructor_id=instructor_id,
        )
        return [
            DailyUsageResponse(
                day=day.date() if hasattr(day, "date") else day,
                conversations=convs,
                questions=questions,
            )
            for day, convs, questions in rows
        ]
