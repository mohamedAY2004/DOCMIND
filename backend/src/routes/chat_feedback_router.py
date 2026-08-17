"""Chat feedback routes (spec §8.4)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import FeedbackReason, FeedbackValue, User, UserRole
from helpers.deps import get_session, require_role, require_student_access
from helpers.config import get_settings
from helpers.errors import APIError, ErrorCode
from schemas.chat import FeedbackRequest, FeedbackResponse, MessageResponse
from schemas.citation import CitationViewResponse
from services.citation_service import CitationService
from services.feedback_service import FeedbackService
from services.message_lifecycle_service import MessageLifecycleService
from services.ephemeral_store import store_for
from services.generation_control import request_cancellation

router = APIRouter(prefix="/chat/messages", tags=["chat", "feedback"])
content_router = APIRouter(prefix="/chat/citations", tags=["chat", "citations"])


@router.post("/{message_id}/cancel", response_model=MessageResponse)
async def cancel_generation(
    message_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
) -> MessageResponse:
    response = await MessageLifecycleService(session).cancel(student, message_id)
    if response.generationStatus == "cancelled":
        await request_cancellation(store_for(request.app), message_id)
    return response


@router.get("/{message_id}/citations/{citation_id}/view", response_model=CitationViewResponse)
async def view_citation(
    message_id: str,
    citation_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_role(UserRole.STUDENT, UserRole.INSTRUCTOR, UserRole.ADMIN)),
) -> CitationViewResponse:
    if not get_settings().STRUCTURED_CITATIONS:
        raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Structured citations are disabled.")
    return await CitationService(session).view(user, message_id, citation_id)


@content_router.get("/content")
async def citation_content(token: str = Query(...), session: AsyncSession = Depends(get_session)):
    path, mime = await CitationService(session).local_content(token)
    return FileResponse(path, media_type=mime, content_disposition_type="inline")


@router.post("/{message_id}/feedback", response_model=FeedbackResponse)
async def create_feedback(
    message_id: str,
    body: FeedbackRequest,
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
) -> FeedbackResponse:
    return await FeedbackService(session).upsert(
        student,
        message_id,
        FeedbackValue(body.feedback),
        FeedbackReason(body.reason) if body.reason else None,
        body.comment,
    )


@router.delete(
    "/{message_id}/feedback",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_feedback(
    message_id: str,
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
) -> None:
    await FeedbackService(session).delete(student, message_id)
