"""Chat feedback routes (spec §8.4)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import FeedbackValue, User, UserRole
from helpers.deps import get_session, require_role, require_student_access
from schemas.chat import FeedbackRequest, FeedbackResponse
from services.feedback_service import FeedbackService

router = APIRouter(prefix="/chat/messages", tags=["chat", "feedback"])


@router.post("/{message_id}/feedback", response_model=FeedbackResponse)
async def create_feedback(
    message_id: str,
    body: FeedbackRequest,
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
) -> FeedbackResponse:
    return await FeedbackService(session).upsert(
        student, message_id, FeedbackValue(body.feedback)
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
