"""Feedback business logic (spec §8.4)."""
from __future__ import annotations

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import FeedbackValue, MessageRole, User
from helpers.errors import APIError, ErrorCode
from repositories.activity_repository import ActivityRepository
from repositories.conversation_repository import ConversationRepository
from repositories.feedback_repository import FeedbackRepository
from repositories.message_repository import MessageRepository
from schemas.chat import FeedbackResponse
from services.activity_logger import ActivityLogger


class FeedbackService:
    def __init__(self, session: AsyncSession) -> None:
        self._feedback = FeedbackRepository(session)
        self._messages = MessageRepository(session)
        self._conversations = ConversationRepository(session)
        self._activity = ActivityLogger(ActivityRepository(session))

    async def _assert_can_feedback(self, caller: User, message_id: str):
        message = await self._messages.get(message_id)
        if message is None:
            raise APIError(
                ErrorCode.NOT_FOUND,
                status.HTTP_404_NOT_FOUND,
                "Message not found.",
            )
        if message.role == MessageRole.USER:
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                status.HTTP_400_BAD_REQUEST,
                "Feedback can only be given on AI replies.",
            )
        conv = await self._conversations.get(message.conversation_id)
        if conv is None or conv.owner_id != caller.id:
            raise APIError(
                ErrorCode.FORBIDDEN,
                status.HTTP_403_FORBIDDEN,
                "You can only give feedback on your own conversations.",
            )
        return message, conv

    async def upsert(
        self, caller: User, message_id: str, value: FeedbackValue
    ) -> FeedbackResponse:
        message, conv = await self._assert_can_feedback(caller, message_id)
        fb = await self._feedback.upsert(
            message_id=message_id, user_id=caller.id, value=value
        )
        if value == FeedbackValue.DOWN:
            await self._activity.record(
                action="AI response flagged",
                actor=caller,
                subject_label=caller.name,
                meta={
                    "conversationId": conv.id,
                    "messageId": message_id,
                    "subjectId": conv.subject_id,
                },
            )
        return FeedbackResponse(
            id=fb.id,
            messageId=fb.message_id,
            feedback=fb.feedback.value,
            createdAt=fb.created_at,
        )

    async def delete(self, caller: User, message_id: str) -> None:
        # Ownership of the feedback *record* is the real guard here — no need to
        # re-run the conversation/AI-reply checks from ``_assert_can_feedback``.
        existing = await self._feedback.get_by_message(message_id)
        if existing is None:
            return  # idempotent: nothing to remove
        if existing.user_id != caller.id:
            raise APIError(
                ErrorCode.FORBIDDEN,
                status.HTTP_403_FORBIDDEN,
                "You can only remove your own feedback.",
            )
        await self._feedback.delete_by_message(message_id)
