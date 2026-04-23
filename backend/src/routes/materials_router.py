"""Material endpoints (spec §7)."""
from __future__ import annotations

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
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, UserRole
from helpers.deps import get_session, require_role
from schemas.material import MaterialResponse, UpdateMaterialRequest
from services.material_service import MaterialService, index_material_job
from services.rag_service import RAGService

router = APIRouter(prefix="/subjects", tags=["materials"])


def _rag_service(request: Request) -> RAGService:
    """Build a ``RAGService`` from the clients stored on ``app.state``."""
    return RAGService(
        vectordb_client=request.app.state.vectordb_client,
        embedding_client=request.app.state.embedding_client,
        generation_client=request.app.state.generation_client,
        template_parser=request.app.state.template_parser,
    )


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
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN)),
) -> None:
    await MaterialService(session).delete(user, subject_id, material_id)
