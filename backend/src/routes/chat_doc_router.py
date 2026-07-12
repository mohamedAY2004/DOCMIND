"""Document-chat routes (spec §8.2)."""
from __future__ import annotations

from typing import List

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, UserRole
from helpers.config import get_settings
from helpers.deps import get_session, require_role, require_student_access
from helpers.pagination import Page, PaginationParams, pagination_query
from schemas.chat import (
    ChatReplyResponse,
    ConversationResponse,
    CreateDocConversationResponse,
    DocumentFileResponse,
    LegacyReplyResponse,
    MessageResponse,
    SendMessageRequest,
    UpdateConversationRequest,
)
from services.document_chat_service import (
    DocumentChatService,
    index_doc_file_job,
)
from services.rag_service import RAGService
from stores.agent import AgentInterface

router = APIRouter(prefix="/chat/doc", tags=["chat", "doc"])
legacy_router = APIRouter(prefix="/chat", tags=["chat", "doc"])


def _rag_service(request: Request) -> RAGService:
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
    response_model=CreateDocConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_doc_conversation(
    request: Request,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
) -> CreateDocConversationResponse:
    service = DocumentChatService(session)
    response, jobs = await service.create_with_files(student, files)
    rag = _rag_service(request)
    for job in jobs:
        background_tasks.add_task(
            index_doc_file_job,
            session_factory=request.app.state.session_maker,
            file_id=job["file_id"],
            conversation_id=job["conversation_id"],
            path=job["path"],
            rag_service=rag,
        )
    return response


@router.get("/conversations", response_model=Page[ConversationResponse])
async def list_doc_conversations(
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
    params: PaginationParams = Depends(pagination_query),
) -> Page[ConversationResponse]:
    return await DocumentChatService(session).list_conversations(student, params)


@router.get(
    "/conversations/{conv_id}/messages", response_model=Page[MessageResponse]
)
async def list_doc_messages(
    conv_id: str,
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
    params: PaginationParams = Depends(pagination_query),
) -> Page[MessageResponse]:
    return await DocumentChatService(session).list_messages(student, conv_id, params)


@router.delete(
    "/conversations/{conv_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_doc_conversation(
    conv_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
) -> None:
    await DocumentChatService(session).delete_conversation(
        student, conv_id, _rag_service(request)
    )


@router.patch(
    "/conversations/{conv_id}",
    response_model=ConversationResponse,
)
async def update_doc_conversation(
    conv_id: str,
    body: UpdateConversationRequest,
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
) -> ConversationResponse:
    return await DocumentChatService(session).update_conversation(
        student, conv_id, body.title
    )


@router.post(
    "/conversations/{conv_id}/files",
    response_model=DocumentFileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_doc_file(
    conv_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
) -> DocumentFileResponse:
    response, job = await DocumentChatService(session).add_file(
        student, conv_id, file
    )
    background_tasks.add_task(
        index_doc_file_job,
        session_factory=request.app.state.session_maker,
        file_id=job["file_id"],
        conversation_id=job["conversation_id"],
        path=job["path"],
        rag_service=_rag_service(request),
    )
    return response


@router.get(
    "/conversations/{conv_id}/files", response_model=List[DocumentFileResponse]
)
async def list_doc_files(
    conv_id: str,
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
) -> List[DocumentFileResponse]:
    return await DocumentChatService(session).list_files(student, conv_id)


@router.delete(
    "/conversations/{conv_id}/files/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_doc_file(
    conv_id: str,
    file_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
) -> None:
    await DocumentChatService(session).remove_file(
        student, conv_id, file_id, _rag_service(request)
    )


@router.post(
    "/conversations/{conv_id}/messages", response_model=ChatReplyResponse
)
async def send_doc_message(
    conv_id: str,
    body: SendMessageRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
) -> ChatReplyResponse:
    return await DocumentChatService(session).send_message(
        student, conv_id, body.message, _rag_service(request), _agent(request)
    )


# -------- Back-compat (spec §8.2.5 note) --------


@legacy_router.post("/doc", response_model=LegacyReplyResponse)
async def legacy_doc_chat(
    body: SendMessageRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _gate: User = Depends(require_student_access),
) -> LegacyReplyResponse:
    reply = await DocumentChatService(session).legacy_doc_reply(
        student, body.message, _rag_service(request), _agent(request)
    )
    return LegacyReplyResponse(reply=reply)
