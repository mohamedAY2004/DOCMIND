"""Data access for :class:`Feedback`."""
from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import func, or_, select, update

from db.models import (
    Conversation,
    Feedback,
    FeedbackValue,
    Message,
    MessageRole,
    Subject,
    User,
)

from .base import BaseRepository


class FeedbackRepository(BaseRepository[Feedback]):
    model = Feedback

    async def get_by_message(self, message_id: str) -> Optional[Feedback]:
        result = await self.session.execute(
            select(Feedback).where(Feedback.message_id == message_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self, *, message_id: str, user_id: str, value: FeedbackValue
    ) -> Feedback:
        existing = await self.get_by_message(message_id)
        if existing is None:
            fb = Feedback(message_id=message_id, user_id=user_id, feedback=value)
            self.session.add(fb)
            await self.session.flush()
            return fb
        await self.session.execute(
            update(Feedback).where(Feedback.id == existing.id).values(feedback=value)
        )
        await self.session.refresh(existing)
        return existing

    async def delete_by_message(self, message_id: str) -> bool:
        existing = await self.get_by_message(message_id)
        if existing is None:
            return False
        await self.session.delete(existing)
        await self.session.flush()
        return True

    async def map_for_messages(self, message_ids: Sequence[str]) -> dict[str, FeedbackValue]:
        """Return {message_id: FeedbackValue} for the given message ids."""
        if not message_ids:
            return {}
        stmt = select(Feedback.message_id, Feedback.feedback).where(
            Feedback.message_id.in_(message_ids)
        )
        rows = (await self.session.execute(stmt)).all()
        return {row.message_id: row.feedback for row in rows}

    async def count_by_subject(
        self, subject_id: str, value: FeedbackValue
    ) -> int:
        stmt = (
            select(func.count(Feedback.id))
            .join(Message, Message.id == Feedback.message_id)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(
                Conversation.subject_id == subject_id,
                Feedback.feedback == value,
            )
        )
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def list_rows(
        self,
        *,
        semester: Optional[str],
        subject_id: Optional[str],
        feedback: Optional[FeedbackValue],
        search: Optional[str],
        offset: int,
        limit: int,
    ) -> tuple[list[dict], int]:
        """Return rows shaped for spec §10.4."""
        from sqlalchemy.orm import aliased

        UserMsg = aliased(Message)

        question_subq = (
            select(UserMsg.text)
            .where(
                UserMsg.conversation_id == Message.conversation_id,
                UserMsg.role == MessageRole.USER,
                UserMsg.created_at < Message.created_at,
            )
            .order_by(UserMsg.created_at.desc())
            .limit(1)
            .correlate(Message)
            .scalar_subquery()
        )

        stmt = (
            select(
                Feedback.id,
                User.name.label("student"),
                User.id.label("student_id"),
                Subject.title.label("subject"),
                Subject.id.label("subject_id"),
                Subject.semester_id.label("semester"),
                question_subq.label("question"),
                Message.text.label("ai_response"),
                Feedback.feedback,
                Feedback.created_at,
            )
            .join(Message, Message.id == Feedback.message_id)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .join(Subject, Subject.id == Conversation.subject_id)
            .join(User, User.id == Feedback.user_id)
        )

        if semester is not None:
            stmt = stmt.where(Subject.semester_id == semester)
        if subject_id is not None:
            stmt = stmt.where(Subject.id == subject_id)
        if feedback is not None:
            stmt = stmt.where(Feedback.feedback == feedback)
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(question_subq).like(like),
                    func.lower(Message.text).like(like),
                )
            )

        total_stmt = (
            select(func.count())
            .select_from(Feedback)
            .join(Message, Message.id == Feedback.message_id)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .join(Subject, Subject.id == Conversation.subject_id)
        )
        if semester is not None:
            total_stmt = total_stmt.where(Subject.semester_id == semester)
        if subject_id is not None:
            total_stmt = total_stmt.where(Subject.id == subject_id)
        if feedback is not None:
            total_stmt = total_stmt.where(Feedback.feedback == feedback)
        total = int((await self.session.execute(total_stmt)).scalar() or 0)

        rows = (
            await self.session.execute(
                stmt.order_by(Feedback.created_at.desc()).offset(offset).limit(limit)
            )
        ).all()

        def _fmt(row) -> dict:
            return {
                "id": row.id,
                "student": row.student,
                "studentId": row.student_id,
                "subject": row.subject,
                "subjectId": row.subject_id,
                "semester": row.semester,
                "question": row.question or "",
                "aiResponse": row.ai_response or "",
                "feedback": row.feedback.value
                if hasattr(row.feedback, "value")
                else row.feedback,
                "timestamp": row.created_at,
            }

        return [_fmt(r) for r in rows], total
