"""Tutor-chat routes (spec §8.1)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, UserRole
from helpers.config import get_settings
from helpers.deps import get_session, require_role, require_student_access
from helpers.pagination import Page, PaginationParams, pagination_query
from schemas.chat import (
    ChatReplyResponse,
    ConversationResponse,
    CreateTutorConversationRequest,
    LegacyReplyResponse,
    MessageResponse,
    SendMessageRequest,
    UpdateConversationRequest,
)
from services.rag_service import RAGService
from services.tutor_chat_service import TutorChatService
from stores.agent import AgentInterface

router = APIRouter(prefix="/chat/tutor", tags=["chat", "tutor"])
legacy_router = APIRouter(prefix="/chat", tags=["chat", "tutor"])


def _rag(request: Request) -> RAGService:
    settings = get_settings()
    return RAGService(
        vectordb_client=request.app.state.vectordb_client,
        embedding_client=request.app.state.embedding_client,
        generation_client=request.app.state.generation_client,
        template_parser=request.app.state.template_parser,
        rerank_client=getattr(request.app.state, "rerank_client", None),
        rerank_overfetch=settings.RERANK_OVERFETCH,
        rerank_top_n=settings.RERANK_TOP_N,
        mmr_enabled=settings.MMR_ENABLED,
        mmr_lambda=settings.MMR_LAMBDA,
        mmr_overfetch=settings.MMR_OVERFETCH,
    )


def _agent(request: Request) -> AgentInterface | None:
    # ``agent_client`` is None when AGENT_ENABLED=false; callers fall
    # back to the classic rag.answer path in that case.
    return getattr(request.app.state, "agent_client", None)


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_tutor_conversation(
    body: CreateTutorConversationRequest,
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
) -> ConversationResponse:
    return await TutorChatService(session).create(student, body.subjectId)


@router.get("/conversations", response_model=Page[ConversationResponse])
async def list_tutor_conversations(
    subjectId: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
    params: PaginationParams = Depends(pagination_query),
) -> Page[ConversationResponse]:
    return await TutorChatService(session).list_conversations(student, subjectId, params)


@router.get(
    "/conversations/{conv_id}/messages", response_model=Page[MessageResponse]
)
async def list_tutor_messages(
    conv_id: str,
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
    params: PaginationParams = Depends(pagination_query),
) -> Page[MessageResponse]:
    return await TutorChatService(session).list_messages(student, conv_id, params)


@router.delete(
    "/conversations/{conv_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_tutor_conversation(
    conv_id: str,
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
) -> None:
    await TutorChatService(session).delete_conversation(student, conv_id)


@router.patch(
    "/conversations/{conv_id}",
    response_model=ConversationResponse,
)
async def update_tutor_conversation(
    conv_id: str,
    body: UpdateConversationRequest,
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
) -> ConversationResponse:
    return await TutorChatService(session).update_conversation(
        student, conv_id, body.title
    )


@router.post(
    "/conversations/{conv_id}/messages", response_model=ChatReplyResponse
)
async def send_tutor_message(
    conv_id: str,
    body: SendMessageRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
) -> ChatReplyResponse:
    return await TutorChatService(session).send_message(
        student, conv_id, body.message, _rag(request), _agent(request)
    )


# -------- Back-compat (spec §8.1.x note) --------


@legacy_router.post("/tutor/{subject_id}", response_model=LegacyReplyResponse)
async def legacy_tutor_chat(
    subject_id: str,
    body: SendMessageRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
) -> LegacyReplyResponse:
    reply = await TutorChatService(session).legacy_subject_reply(
        student, subject_id, body.message, _rag(request), _agent(request)
    )
    return LegacyReplyResponse(reply=reply)
