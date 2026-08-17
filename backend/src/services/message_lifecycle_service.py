"""Ownership-checked lifecycle operations for generated replies."""
from __future__ import annotations

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import GenerationStatus, MessageRole, User
from helpers.errors import APIError, ErrorCode
from repositories.conversation_repository import ConversationRepository
from repositories.message_repository import MessageRepository
from schemas.chat import MessageResponse
from services.telemetry_service import metrics


class MessageLifecycleService:
    def __init__(self, session: AsyncSession) -> None:
        self._messages = MessageRepository(session)
        self._conversations = ConversationRepository(session)

    async def cancel(self, caller: User, reply_id: str) -> MessageResponse:
        reply = await self._messages.get(reply_id)
        if reply is None or reply.role == MessageRole.USER:
            raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Reply not found.")
        conv = await self._conversations.get(reply.conversation_id)
        if conv is None or conv.owner_id != caller.id:
            raise APIError(
                ErrorCode.FORBIDDEN,
                status.HTTP_403_FORBIDDEN,
                "You can only cancel replies in your own conversations.",
            )
        if await self._messages.cancel_if_generating(reply.id):
            metrics.increment("generation_cancelled_total")
            await self._messages.session.refresh(reply)
        return MessageResponse(
            id=reply.id,
            role=reply.role.value,
            text=reply.text,
            createdAt=reply.created_at,
            citations=reply.citations or [],
            generationStatus=reply.generation_status.value,
            groundingStatus=(reply.grounding_status.value if reply.grounding_status else None),
        )
