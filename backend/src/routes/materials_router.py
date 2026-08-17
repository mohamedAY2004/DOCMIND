"""Material endpoints (spec §7) + instructor test-bot."""
from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from starlette.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import SemesterState, User, UserRole
from helpers.config import get_settings
from helpers.deps import get_session, require_role
from helpers.errors import APIError, ErrorCode
from repositories.material_repository import MaterialRepository
from repositories.subject_repository import SubjectRepository
from schemas.material import MaterialResponse, UpdateMaterialRequest
from services.material_service import MaterialService, index_material_job
from services.answer_result import AnswerResult, result_from_generation
from services.ephemeral_store import store_for
from services.generation_control import GenerationSlot
from services.rag_service import RAGService, collection_for_subject
from services.sse import encode_sse
from stores.agent import AgentInterface

logger = logging.getLogger("docmind.materials")

router = APIRouter(prefix="/subjects", tags=["materials"])


def _rag_service(request: Request) -> RAGService:
    """Build a ``RAGService`` from the clients stored on ``app.state``."""
    return RAGService(
        vectordb_client=request.app.state.vectordb_client,
        embedding_client=request.app.state.embedding_client,
        generation_client=request.app.state.generation_client,
        template_parser=request.app.state.template_parser,
    )


def _agent(request: Request) -> AgentInterface | None:
    return getattr(request.app.state, "agent_client", None)


# -------------------- materials CRUD --------------------


@router.get("/{subject_id}/materials", response_model=List[MaterialResponse])
async def list_materials(
    subject_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN)),
) -> List[MaterialResponse]:
    return await MaterialService(session).list_for_subject(user, subject_id)


@router.post(
    "/{subject_id}/materials",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_material(
    subject_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile,
    name: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_role(UserRole.INSTRUCTOR)),
) -> MaterialResponse:
    service = MaterialService(session)
    response, job = await service.upload(user, subject_id, file, name)
    # Schedule indexing AFTER response is returned so the client doesn't wait.
    background_tasks.add_task(
        index_material_job,
        session_factory=request.app.state.session_maker,
        material_id=job["material_id"],
        subject_id=job["subject_id"],
        path=job["path"],
        rag_service=_rag_service(request),
    )
    return response


@router.patch(
    "/{subject_id}/materials/{material_id}", response_model=MaterialResponse
)
async def patch_material(
    subject_id: str,
    material_id: str,
    body: UpdateMaterialRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN)),
) -> MaterialResponse:
    return await MaterialService(session).patch(
        user,
        subject_id,
        material_id,
        name=body.name,
        status_value=body.status,
    )


@router.delete(
    "/{subject_id}/materials/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_material(
    subject_id: str,
    material_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN)),
) -> None:
    await MaterialService(session).delete(
        user, subject_id, material_id, _rag_service(request)
    )


@router.get("/{subject_id}/materials/{material_id}/download")
async def download_material(
    subject_id: str,
    material_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN)),
) -> Response:
    """Download a previously uploaded material file.

    Allowed for any instructor on the roster (super or viewer) and admins,
    including on archived semesters — downloading old content is the only
    action that remains available once a term is archived.
    """
    target, filename, media_type, is_remote = await MaterialService(session).get_download(
        user, subject_id, material_id
    )
    if is_remote:
        return RedirectResponse(target, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    return FileResponse(target, media_type=media_type, filename=filename)


# -------------------- instructor test-bot --------------------


class _TestBotRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class _TestBotResponse(BaseModel):
    reply: str


@router.post("/{subject_id}/test-bot/stream")
async def stream_test_bot(
    subject_id: str,
    body: _TestBotRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN)),
) -> StreamingResponse:
    """Stream the stateless instructor preview through the production RAG path."""
    if not get_settings().STREAMING_CHAT:
        raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Streaming chat is disabled.")
    subjects = SubjectRepository(session)
    subject = await subjects.get(subject_id)
    if subject is None:
        raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Subject not found.")
    if user.role != UserRole.ADMIN and not await subjects.is_instructor_of(subject_id, user.id):
        raise APIError(ErrorCode.FORBIDDEN, status.HTTP_403_FORBIDDEN, "You are not assigned to this subject.")
    if await subjects.semester_state_for_subject(subject_id) is SemesterState.ARCHIVED:
        raise APIError(ErrorCode.FORBIDDEN, status.HTTP_403_FORBIDDEN, "This semester is archived; the assistant is offline and cannot be tested.")
    if await MaterialRepository(session).count_processed(subject_id) == 0:
        raise APIError(ErrorCode.SUBJECT_NOT_READY, status.HTTP_409_CONFLICT, "This subject has no indexed materials yet. Upload and wait for processing to finish.")

    reply_id = "preview_" + uuid.uuid4().hex[:20]
    subject_name = f"{subject.course_code} - {subject.title}"
    rag = _rag_service(request)
    agent = _agent(request)
    store = store_for(request.app)
    slot = await GenerationSlot.acquire(store, user.id)

    async def events():
        try:
            yield encode_sse("message.created", {"reply": {"id": reply_id, "role": "assistant", "text": "", "citations": [], "generationStatus": "generating", "groundingStatus": None}})
            result = None
            collection = collection_for_subject(subject_id)
            if agent is not None and hasattr(agent, "answer_stream"):
                settings = get_settings()
                agent_result = None
                async for kind, payload in agent.answer_stream(
                    collection_name=collection,
                    query=body.message,
                    rag_service=rag,
                    history=None,
                    subject_name=subject_name,
                    limit=settings.AGENT_RETRIEVAL_LIMIT,
                    threshold=settings.AGENT_RETRIEVAL_THRESHOLD,
                ):
                    if kind == "delta":
                        yield encode_sse("answer.delta", {"replyId": reply_id, "delta": payload})
                    else:
                        agent_result = payload
                if agent_result is not None:
                    result = (
                        result_from_generation(agent_result.text, agent_result.retrieved, source_kind="material")
                        if agent_result.retrieved
                        else AnswerResult(
                            text=agent_result.text,
                            grounding_status="no_context" if agent_result.used_retrieval else "ungrounded",
                        )
                    )
            else:
                async for kind, payload in rag.answer_stream(
                    collection,
                    body.message,
                    limit=5,
                    threshold=0.3,
                    subject_name=subject_name,
                ):
                    if kind == "delta":
                        yield encode_sse("answer.delta", {"replyId": reply_id, "delta": payload})
                    else:
                        result = payload
            if result is None:
                raise RuntimeError("Generation completed without a result")
            yield encode_sse("answer.citations", {"replyId": reply_id, "citations": result.citations, "groundingStatus": result.grounding_status})
            yield encode_sse("answer.completed", {"reply": {"id": reply_id, "role": "assistant", "text": result.text, "citations": result.citations, "generationStatus": "complete", "groundingStatus": result.grounding_status}})
        except Exception as exc:  # noqa: BLE001
            logger.exception("Instructor preview generation failed")
            yield encode_sse("answer.failed", {"replyId": reply_id, "code": "GENERATION_FAILED", "message": str(exc)})
        finally:
            await slot.release()

    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post(
    "/{subject_id}/test-bot",
    response_model=_TestBotResponse,
    tags=["materials", "test-bot"],
)
async def test_bot(
    subject_id: str,
    body: _TestBotRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN)),
) -> _TestBotResponse:
    """Stateless bot preview for instructors.

    Queries the subject's RAG collection using the same pipeline students
    use, but does NOT persist any conversation or messages.
    """
    # Verify the subject exists.
    subjects = SubjectRepository(session)
    subject = await subjects.get(subject_id)
    if subject is None:
        raise APIError(
            ErrorCode.NOT_FOUND,
            status.HTTP_404_NOT_FOUND,
            "Subject not found.",
        )

    # Archived semesters take the bot offline — no testing on past terms.
    state = await subjects.semester_state_for_subject(subject_id)
    if state is SemesterState.ARCHIVED:
        raise APIError(
            ErrorCode.FORBIDDEN,
            status.HTTP_403_FORBIDDEN,
            "This semester is archived; the assistant is offline and cannot be tested.",
            details={"semesterState": state.value},
        )

    # Check for indexed materials.
    processed = await MaterialRepository(session).count_processed(subject_id)
    if processed == 0:
        raise APIError(
            ErrorCode.SUBJECT_NOT_READY,
            status.HTTP_409_CONFLICT,
            "This subject has no indexed materials yet. Upload and wait for processing to finish.",
        )

    subject_name = f"{subject.course_code} — {subject.title}" if subject else "Unknown"
    collection = collection_for_subject(subject_id)
    rag = _rag_service(request)
    agent = _agent(request)
    slot = await GenerationSlot.acquire(store_for(request.app), user.id)

    try:
        if agent is not None:
            settings = get_settings()
            result = await agent.answer(
                collection_name=collection,
                query=body.message,
                rag_service=rag,
                history=None,
                subject_name=subject_name,
                limit=settings.AGENT_RETRIEVAL_LIMIT,
                threshold=settings.AGENT_RETRIEVAL_THRESHOLD,
            )
            answer = result.text or ""
        else:
            answer = (await rag.answer(
                collection, body.message, limit=5, threshold=0.3,
                subject_name=subject_name,
            )).text
    finally:
        await slot.release()

    return _TestBotResponse(reply=answer)
