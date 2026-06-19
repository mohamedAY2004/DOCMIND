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
        all_subjects = await self._subjects.list_all()
        total = len(all_subjects)
        window = all_subjects[params.offset : params.offset + params.page_size]
        items: List[SubjectStatsResponse] = []
        for s in window:
            items.append(await self._single_subject_stats(s))
        return Page.build(items=items, total=total, params=params)

    async def _single_subject_stats(self, subject: Subject) -> SubjectStatsResponse:
        counts = (
            await self._session.execute(
                select(
                    func.count(Material.id).label("total"),
                    func.count(Material.id).filter(
                        Material.status == MaterialStatus.PROCESSED
                    ).label("processed"),
                ).where(Material.subject_id == subject.id)
            )
        ).one()
        total_mat = int(counts.total or 0)
        processed = int(counts.processed or 0)
        if total_mat == 0:
            mat_status = "empty"
        elif processed == total_mat:
            mat_status = "processed"
        elif processed == 0:
            mat_status = "indexing"
        else:
            mat_status = "mixed"

        interactions = int(
            (
                await self._session.execute(
                    select(func.count(Conversation.id)).where(
                        Conversation.subject_id == subject.id,
                        Conversation.kind == ConversationKind.TUTOR,
                    )
                )
            ).scalar()
            or 0
        )
        ai_responses = int(
            (
                await self._session.execute(
                    select(func.count(Message.id))
                    .join(Conversation, Conversation.id == Message.conversation_id)
                    .where(
                        Conversation.subject_id == subject.id,
                        Message.role == MessageRole.ASSISTANT,
                    )
                )
            ).scalar()
            or 0
        )
        feedback_counts = (
            await self._session.execute(
                select(
                    func.count(Feedback.id)
                    .filter(Feedback.feedback == FeedbackValue.UP)
                    .label("up"),
                    func.count(Feedback.id)
                    .filter(Feedback.feedback == FeedbackValue.DOWN)
                    .label("down"),
                )
                .select_from(Feedback)
                .join(Message, Message.id == Feedback.message_id)
                .join(Conversation, Conversation.id == Message.conversation_id)
                .where(Conversation.subject_id == subject.id)
            )
        ).one()
        instructor_ids = await self._subjects.instructor_ids(subject.id)
        super_instructor = await self._subjects.get_super_instructor(subject.id)
        return SubjectStatsResponse(
            id=subject.id,
            title=subject.title,
            semester=subject.semester_id,
            pdfCount=total_mat,
            materialStatus=mat_status,
            interactions=interactions,
            aiResponses=ai_responses,
            thumbsUp=int(feedback_counts.up or 0),
            thumbsDown=int(feedback_counts.down or 0),
            instructorIds=instructor_ids,
            superInstructorId=super_instructor.id if super_instructor else None,
        )

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
