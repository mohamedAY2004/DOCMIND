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
from schemas.material import MaterialResponse, UpdateMaterialRequest, TestBotRequest, TestBotResponse
from services.preview_service import PreviewService
from services.material_service import MaterialService, index_material_job
from services.answer_result import AnswerResult, result_from_generation
from services.ephemeral_store import store_for
from services.generation_control import GenerationSlot
from services.rag_runtime import rag_from_state
from services.rag_service import RAGService, collection_for_subject
from services.sse import encode_sse
from stores.agent import AgentInterface

logger = logging.getLogger("docmind.materials")

router = APIRouter(prefix="/subjects", tags=["materials"])




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
        rag_service=rag_from_state(request.app.state),
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
        user, subject_id, material_id, rag_from_state(request.app.state)
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


@router.post("/{subject_id}/test-bot/stream")
async def stream_test_bot(subject_id: str, body: TestBotRequest, request: Request,
                          session: AsyncSession = Depends(get_session),
                          user: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN))):
    events = await PreviewService(session, rag_from_state(request.app.state),
                                  _agent(request), store_for(request.app)).stream(user, subject_id, body.message)
    async def encoded():
        async for event, payload in events:
            yield encode_sse(event, payload)
    return StreamingResponse(encoded(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/{subject_id}/test-bot", response_model=TestBotResponse)
async def test_bot(subject_id: str, body: TestBotRequest, request: Request,
                   session: AsyncSession = Depends(get_session),
                   user: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN))):
    return await PreviewService(session, rag_from_state(request.app.state),
                                _agent(request), store_for(request.app)).reply(user, subject_id, body.message)
