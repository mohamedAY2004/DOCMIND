"""Data access for :class:`Message`."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import func, select

from db.models import (
    Conversation,
    Message,
    MessageRole,
    Subject,
    SubjectInstructor,
)

from .base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    model = Message

    async def get(self, message_id: str) -> Optional[Message]:
        return await self.session.get(Message, message_id)

    async def add(self, msg: Message) -> Message:
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def list_for_conversation(
        self, conv_id: str, offset: int, limit: int
    ) -> tuple[Sequence[Message], int]:
        total_stmt = select(func.count(Message.id)).where(
            Message.conversation_id == conv_id
        )
        total = int((await self.session.execute(total_stmt)).scalar() or 0)
        rows = (
            await self.session.execute(
                select(Message)
                .where(Message.conversation_id == conv_id)
                .order_by(Message.created_at.asc())
                .offset(offset)
                .limit(limit)
            )
        ).scalars().all()
        return rows, total

    async def history(self, conv_id: str, limit: int = 20) -> Sequence[Message]:
        """Return the most-recent ``limit`` messages in chronological order.

        Fetch newest-first with the LIMIT (so we keep the *latest* turns, not
        the opening ones), then reverse so callers still receive them oldest →
        newest for the agent prompt.
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conv_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))

    async def count_since(
        self, role: MessageRole, since: datetime
    ) -> int:
        result = await self.session.execute(
            select(func.count(Message.id)).where(
                Message.role == role, Message.created_at >= since
            )
        )
        return int(result.scalar() or 0)

    async def daily_rollup(
        self,
        since: datetime,
        *,
        subject_id: Optional[str] = None,
        semester_id: Optional[str] = None,
        instructor_id: Optional[str] = None,
    ) -> Sequence[tuple[datetime, int, int]]:
        """Return ``(day, distinct_conversations, user_message_count)`` per day.

        Optional ``subject_id`` / ``semester_id`` / ``instructor_id`` scope the
        rollup to conversations belonging to the matching subject(s).
        """
        day_col = func.date_trunc("day", Message.created_at).label("day")
        stmt = select(
            day_col,
            func.count(func.distinct(Message.conversation_id)).label("convs"),
            func.count(Message.id)
            .filter(Message.role == MessageRole.USER)
            .label("questions"),
        ).where(Message.created_at >= since)

        if subject_id or semester_id or instructor_id:
            stmt = stmt.join(Conversation, Conversation.id == Message.conversation_id)
        if subject_id:
            stmt = stmt.where(Conversation.subject_id == subject_id)
        if semester_id:
            stmt = stmt.join(Subject, Subject.id == Conversation.subject_id).where(
                Subject.semester_id == semester_id
            )
        if instructor_id:
            subj_subq = select(SubjectInstructor.subject_id).where(
                SubjectInstructor.user_id == instructor_id
            )
            stmt = stmt.where(Conversation.subject_id.in_(subj_subq))

        stmt = stmt.group_by(day_col).order_by(day_col)
        result = await self.session.execute(stmt)
        return [(row.day, int(row.convs or 0), int(row.questions or 0)) for row in result]

    async def previous_user_message(
        self, conv_id: str, before: datetime
    ) -> Optional[Message]:
        result = await self.session.execute(
            select(Message)
            .where(
                Message.conversation_id == conv_id,
                Message.role == MessageRole.USER,
                Message.created_at < before,
            )
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
