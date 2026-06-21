"""Tutor-chat business logic (spec §8.1)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    Conversation,
    ConversationKind,
    Message,
    MessageRole,
    SemesterState,
    User,
    UserRole,
)
from helpers.config import get_settings
from helpers.errors import APIError, ErrorCode
from helpers.pagination import Page, PaginationParams
from repositories.conversation_repository import ConversationRepository
from repositories.feedback_repository import FeedbackRepository
from repositories.material_repository import MaterialRepository
from repositories.message_repository import MessageRepository
from repositories.subject_repository import SubjectRepository
from schemas.chat import (
    ChatReplyResponse,
    ConversationResponse,
    MessageResponse,
)
from services.rag_service import RAGService, collection_for_subject
from stores.agent import AgentInterface

logger = logging.getLogger("docmind.tutor_chat")


class TutorChatService:
    def __init__(self, session: AsyncSession) -> None:
        self._conversations = ConversationRepository(session)
        self._messages = MessageRepository(session)
        self._subjects = SubjectRepository(session)
        self._materials = MaterialRepository(session)
        self._feedback = FeedbackRepository(session)

    async def _load_owned(self, owner: User, conv_id: str) -> Conversation:
        conv = await self._conversations.get(conv_id)
        if conv is None or conv.kind != ConversationKind.TUTOR:
            raise APIError(
                ErrorCode.NOT_FOUND,
                status.HTTP_404_NOT_FOUND,
                "Tutor conversation not found.",
            )
        if conv.owner_id != owner.id:
            raise APIError(
                ErrorCode.FORBIDDEN,
                status.HTTP_403_FORBIDDEN,
                "You do not own this conversation.",
            )
        return conv

    async def _ensure_subject_ready(self, subject_id: str) -> None:
        subject = await self._subjects.get(subject_id)
        if subject is None:
            raise APIError(
                ErrorCode.NOT_FOUND,
                status.HTTP_404_NOT_FOUND,
                "Subject not found.",
            )
        processed = await self._materials.count_processed(subject_id)
        if processed == 0:
            raise APIError(
                ErrorCode.SUBJECT_NOT_READY,
                status.HTTP_409_CONFLICT,
                "This subject has no indexed materials yet.",
            )

    # Cap the number of material names injected into the prompt so a subject
    # with a huge corpus can't crowd out retrieved context on a small model.
    _MANIFEST_MAX_ITEMS = 30

    async def _build_corpus(
        self, subject_id: str
    ) -> tuple[str, list[tuple[str, str]]]:
        """Return ``(manifest_text, [(material_id, name), ...])`` for a subject.

        The text is injected into the prompts; the ``(id, name)`` list is the
        allowlist the planner's source filter is validated/resolved against.
        ``manifest_text`` is ``""`` when there are no processed materials so the
        template's ``$subject_manifest`` slot collapses cleanly.
        """
        materials = await self._materials.processed_materials_for_subject(subject_id)
        if not materials:
            return "", []
        shown = list(materials[: self._MANIFEST_MAX_ITEMS])
        lines = ["The following materials are indexed for this subject:"]
        lines.extend(f"  - {name}" for _id, name in shown)
        if len(materials) > len(shown):
            lines.append(f"  - ...and {len(materials) - len(shown)} more.")
        lines.append(
            "Only these materials are available to retrieve from. If a topic is "
            "not covered by them, say so instead of inventing an answer."
        )
        return "\n".join(lines), list(materials)

    async def _ensure_student_enrolled(self, user: User, subject_id: str) -> None:
        """Students may only tutor on subjects they're enrolled in."""
        if user.role != UserRole.STUDENT:
            return
        if not await self._subjects.is_student_of(subject_id, user.id):
            raise APIError(
                ErrorCode.FORBIDDEN,
                status.HTTP_403_FORBIDDEN,
                "You are not enrolled in this subject.",
            )

    async def _ensure_subject_interactive(self, user: User, subject_id: str) -> None:
        """Students may only start *new* tutor turns on a currently-active semester.

        Past-/future-semester subjects stay readable — ``_load_owned`` gates
        reads on conversation ownership, not enrollment or semester — but reject
        new conversations and messages, so a student can review history without
        resurrecting an archived course. Non-students (e.g. staff previewing the
        tutor) pass, mirroring ``_ensure_student_enrolled``.
        """
        if user.role != UserRole.STUDENT:
            return
        state = await self._subjects.semester_state_for_subject(subject_id)
        if state is SemesterState.ACTIVE:
            return
        message = (
            "This semester is archived; you can review past conversations "
            "but cannot start new chats."
            if state is SemesterState.ARCHIVED
            else "This semester has not started yet."
        )
        raise APIError(
            ErrorCode.FORBIDDEN,
            status.HTTP_403_FORBIDDEN,
            message,
            details={"semesterState": state.value},
        )

    async def create(self, owner: User, subject_id: str) -> ConversationResponse:
        await self._ensure_subject_ready(subject_id)
        await self._ensure_student_enrolled(owner, subject_id)
        await self._ensure_subject_interactive(owner, subject_id)
        count = await self._conversations.count_for_owner(
            owner_id=owner.id,
            kind=ConversationKind.TUTOR,
            subject_id=subject_id,
        )

        conv = Conversation(
            owner_id=owner.id,
            kind=ConversationKind.TUTOR,
            subject_id=subject_id,
            title=f"Chat {count + 1}",
        )
        await self._conversations.add(conv)
        return _conv_response(conv, 0)

    async def list_conversations(
        self, owner: User, subject_id: str | None, params: PaginationParams
    ) -> Page[ConversationResponse]:
        rows, total = await self._conversations.list_for_owner(
            owner_id=owner.id,
            kind=ConversationKind.TUTOR,
            subject_id=subject_id,
            offset=params.offset,
            limit=params.page_size,
        )
        counts = await self._conversations.message_counts([c.id for c in rows])
        items = [_conv_response(c, counts.get(c.id, 0)) for c in rows]
        return Page.build(items=items, total=total, params=params)

    async def list_messages(
        self, owner: User, conv_id: str, params: PaginationParams
    ) -> Page[MessageResponse]:
        conv = await self._load_owned(owner, conv_id)
        rows, total = await self._messages.list_for_conversation(
            conv.id, offset=params.offset, limit=params.page_size
        )
        ai_ids = [m.id for m in rows if m.role != MessageRole.USER]
        fb_map = await self._feedback.map_for_messages(ai_ids)
        items = []
        for m in rows:
            resp = _message_response(m)
            fb = fb_map.get(m.id)
            if fb is not None:
                resp.feedback = fb.value
            items.append(resp)
        return Page.build(items=items, total=total, params=params)

    async def delete_conversation(self, owner: User, conv_id: str) -> None:
        conv = await self._load_owned(owner, conv_id)
        await self._conversations.delete(conv)

    async def update_conversation(
        self, owner: User, conv_id: str, title: str | None
    ) -> ConversationResponse:
        conv = await self._load_owned(owner, conv_id)
        if title is not None:
            conv.title = title
            conv.updated_at = datetime.now(timezone.utc)
        count = await self._conversations.message_count(conv.id)
        return _conv_response(conv, count)

    async def send_message(
        self,
        owner: User,
        conv_id: str,
        text: str,
        rag: RAGService,
        agent: Optional[AgentInterface] = None,
    ) -> ChatReplyResponse:
        conv = await self._load_owned(owner, conv_id)
        if not text.strip():
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                status.HTTP_400_BAD_REQUEST,
                "Message cannot be empty.",
            )
        await self._ensure_subject_ready(conv.subject_id or "")
        await self._ensure_student_enrolled(owner, conv.subject_id or "")
        await self._ensure_subject_interactive(owner, conv.subject_id or "")

        # Build a human-readable subject label for prompt scoping.
        subject = await self._subjects.get(conv.subject_id or "")
        subject_name = (
            f"{subject.course_code} \u2014 {subject.title}" if subject else "Unknown"
        )
        subject_manifest, material_index = await self._build_corpus(
            conv.subject_id or ""
        )

        # Capture history BEFORE persisting the new user message so the
        # planner sees the conversation as it was before this turn.
        history_turns = get_settings().AGENT_HISTORY_TURNS
        history = (
            await self._recent_history(conv.id, history_turns)
            if agent is not None and history_turns > 0
            else None
        )

        user_msg = Message(conversation_id=conv.id, role=MessageRole.USER, text=text)
        await self._messages.add(user_msg)

        collection = collection_for_subject(conv.subject_id or "")
        if agent is not None:
            settings = get_settings()
            result = await agent.answer(
                collection_name=collection,
                query=text,
                rag_service=rag,
                history=history,
                subject_name=subject_name,
                subject_manifest=subject_manifest,
                material_index=material_index,
                source_filter_enabled=settings.AGENT_SOURCE_FILTER_ENABLED,
                limit=settings.AGENT_RETRIEVAL_LIMIT,
                threshold=settings.AGENT_RETRIEVAL_THRESHOLD,
            )
            answer = result.text
            logger.info(
                "agent.tutor_chat conv=%s used_retrieval=%s planner_query=%r hits=%d sources=%s",
                conv.id,
                result.used_retrieval,
                result.planner_query,
                len(result.retrieved),
                result.sources_filter,
            )
        else:
            answer = await rag.answer(
                collection,
                text,
                limit=5,
                threshold=0.3,
                subject_name=subject_name,
                subject_manifest=subject_manifest,
            )
        reply = Message(
            conversation_id=conv.id, role=MessageRole.ASSISTANT, text=answer or ""
        )
        await self._messages.add(reply)

        conv.updated_at = datetime.now(timezone.utc)

        return ChatReplyResponse(
            userMessage=_message_response(user_msg),
            reply=_message_response(reply),
        )

    async def legacy_subject_reply(
        self,
        owner: User,
        subject_id: str,
        text: str,
        rag: RAGService,
        agent: Optional[AgentInterface] = None,
    ) -> str:
        """Back-compat: ``POST /chat/tutor/:subjectId`` with no conversation."""
        await self._ensure_subject_ready(subject_id)
        await self._ensure_student_enrolled(owner, subject_id)
        await self._ensure_subject_interactive(owner, subject_id)
        collection = collection_for_subject(subject_id)

        # Build a human-readable subject label for prompt scoping.
        subject = await self._subjects.get(subject_id)
        subject_name = (
            f"{subject.course_code} \u2014 {subject.title}" if subject else "Unknown"
        )
        subject_manifest, material_index = await self._build_corpus(subject_id)

        if agent is not None:
            settings = get_settings()
            result = await agent.answer(
                collection_name=collection,
                query=text,
                rag_service=rag,
                history=None,
                subject_name=subject_name,
                subject_manifest=subject_manifest,
                material_index=material_index,
                source_filter_enabled=settings.AGENT_SOURCE_FILTER_ENABLED,
                limit=settings.AGENT_RETRIEVAL_LIMIT,
                threshold=settings.AGENT_RETRIEVAL_THRESHOLD,
            )
            return result.text or ""
        return await rag.answer(
            collection,
            text,
            limit=5,
            threshold=0.3,
            subject_name=subject_name,
            subject_manifest=subject_manifest,
        )

    async def _recent_history(
        self, conv_id: str, limit: int
    ) -> list[dict]:
        """Fetch the last N messages and shape them for the planner.

        Returns a generic ``[{"role": "...", "content": "..."}]`` list; the
        strategy adapts this into its provider's wire format.
        """
        if limit <= 0:
            return []
        rows = await self._messages.history(conv_id, limit=limit)
        out: list[dict] = []
        for m in rows:
            role = "assistant" if m.role != MessageRole.USER else "user"
            out.append({"role": role, "content": m.text or ""})
        return out


def _conv_response(conv: Conversation, count: int) -> ConversationResponse:
    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        subjectId=conv.subject_id,
        createdAt=conv.created_at,
        updatedAt=conv.updated_at,
        messageCount=count,
    )


def _message_response(msg: Message) -> MessageResponse:
    return MessageResponse(
        id=msg.id,
        role=msg.role.value,
        text=msg.text,
        createdAt=msg.created_at,
    )
