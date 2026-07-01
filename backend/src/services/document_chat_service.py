"""Document chat business logic (spec §8.2)."""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Sequence

import aiofiles
from fastapi import UploadFile, status
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from db.models import (
    Conversation,
    ConversationKind,
    DocumentFile,
    DocumentFileStatus,
    Message,
    MessageRole,
    User,
)
from helpers.config import get_settings
from helpers.errors import APIError, ErrorCode
from helpers.pagination import Page, PaginationParams
from repositories.conversation_repository import ConversationRepository
from repositories.document_file_repository import DocumentFileRepository
from repositories.message_repository import MessageRepository
from schemas.chat import (
    ChatReplyResponse,
    ConversationResponse,
    CreateDocConversationResponse,
    DocumentFileResponse,
    MessageResponse,
)
from services.file_service import (
    clean_filename,
    doc_files_dir,
    ext_of,
    random_suffix,
    validate_doc_upload,
)
from services.ingestion_service import detect_pdf_encrypted, ingest_file
from services.rag_service import RAGService, collection_for_conversation
from stores.agent import AgentInterface

logger = logging.getLogger("docmind.doc_chat")


class DocumentChatService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._conversations = ConversationRepository(session)
        self._files = DocumentFileRepository(session)
        self._messages = MessageRepository(session)

    # ---------- conversation ownership ----------

    async def _load_owned(self, owner: User, conv_id: str) -> Conversation:
        conv = await self._conversations.get(conv_id)
        if conv is None or conv.kind != ConversationKind.DOC:
            raise APIError(
                ErrorCode.NOT_FOUND,
                status.HTTP_404_NOT_FOUND,
                "Document conversation not found.",
            )
        if conv.owner_id != owner.id:
            raise APIError(
                ErrorCode.FORBIDDEN,
                status.HTTP_403_FORBIDDEN,
                "You do not own this conversation.",
            )
        return conv

    # ---------- commands ----------

    async def create_with_files(
        self, owner: User, uploads: Sequence[UploadFile]
    ) -> tuple[CreateDocConversationResponse, list[dict]]:
        if not uploads:
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                status.HTTP_400_BAD_REQUEST,
                "At least one file is required.",
            )
        settings = get_settings()
        if len(uploads) > settings.UPLOAD_DOC_MAX_FILES:
            raise APIError(
                ErrorCode.FILE_LIMIT,
                status.HTTP_409_CONFLICT,
                f"You can attach at most {settings.UPLOAD_DOC_MAX_FILES} files.",
            )
        for f in uploads:
            validate_doc_upload(f)

        count = await self._conversations.count_for_owner(
            owner_id=owner.id,
            kind=ConversationKind.DOC
        )

        conv = Conversation(
            owner_id=owner.id, kind=ConversationKind.DOC, title=f"Chat {count + 1}"
        )
        await self._conversations.add(conv)

        files, jobs = [], []
        for up in uploads:
            saved, job = await self._save_file(conv.id, up)
            files.append(saved)
            jobs.append(job)

        response = CreateDocConversationResponse(
            conversation=_conv_response(conv, 0),
            files=[_file_response(f) for f in files],
        )
        return response, jobs

    async def add_file(
        self, owner: User, conv_id: str, upload: UploadFile
    ) -> tuple[DocumentFileResponse, dict]:
        conv = await self._load_owned(owner, conv_id)
        existing = await self._files.count_for_conversation(conv.id)
        if existing >= get_settings().UPLOAD_DOC_MAX_FILES:
            raise APIError(
                ErrorCode.FILE_LIMIT,
                status.HTTP_409_CONFLICT,
                "File limit reached for this conversation.",
            )
        validate_doc_upload(upload)
        saved, job = await self._save_file(conv.id, upload)
        return _file_response(saved), job

    async def remove_file(
        self, owner: User, conv_id: str, file_id: str, rag: RAGService
    ) -> None:
        conv = await self._load_owned(owner, conv_id)
        all_files = await self._files.list_for_conversation(conv.id)
        if len(all_files) <= 1:
            raise APIError(
                ErrorCode.CONFLICT,
                status.HTTP_409_CONFLICT,
                "Cannot remove the last file from a conversation.",
            )
        target = next((f for f in all_files if f.id == file_id), None)
        if target is None:
            raise APIError(
                ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "File not found."
            )
        await self._files.delete(target)
        # Evict the file's chunks from the conversation's collection so chat
        # stops answering from removed documents. Runs before the request
        # commits: a failure rolls the row delete back so removal can be retried.
        await rag.delete_material(collection_for_conversation(conv.id), file_id)
        if target.storage_path and os.path.exists(target.storage_path):
            try:
                os.unlink(target.storage_path)
            except OSError:
                logger.warning("Failed to delete %s", target.storage_path)

    async def list_files(
        self, owner: User, conv_id: str
    ) -> List[DocumentFileResponse]:
        conv = await self._load_owned(owner, conv_id)
        rows = await self._files.list_for_conversation(conv.id)
        return [_file_response(f) for f in rows]

    async def list_conversations(
        self, owner: User, params: PaginationParams
    ) -> Page[ConversationResponse]:
        rows, total = await self._conversations.list_for_owner(
            owner_id=owner.id,
            kind=ConversationKind.DOC,
            subject_id=None,
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
        items = [_message_response(m) for m in rows]
        return Page.build(items=items, total=total, params=params)

    async def delete_conversation(
        self, owner: User, conv_id: str, rag: RAGService
    ) -> None:
        conv = await self._load_owned(owner, conv_id)
        files = await self._files.list_for_conversation(conv.id)
        for f in files:
            if f.storage_path and os.path.exists(f.storage_path):
                try:
                    os.unlink(f.storage_path)
                except OSError:
                    pass
        await rag.delete_collection(collection_for_conversation(conv.id))
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
        still_processing = await self._files.count_still_processing(conv.id)
        if still_processing > 0:
            raise APIError(
                ErrorCode.FILES_NOT_READY,
                status.HTTP_409_CONFLICT,
                "Some files are still being processed. Please wait.",
            )
        if not text.strip():
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                status.HTTP_400_BAD_REQUEST,
                "Message cannot be empty.",
            )

        # Capture history BEFORE persisting the new user message so the
        # planner sees the conversation as it was when the student hit send.
        history_turns = get_settings().AGENT_HISTORY_TURNS
        history = (
            await self._recent_history(conv.id, history_turns)
            if agent is not None and history_turns > 0
            else None
        )

        user_msg = Message(conversation_id=conv.id, role=MessageRole.USER, text=text)
        await self._messages.add(user_msg)

        collection = collection_for_conversation(conv.id)
        if agent is not None:
            settings = get_settings()
            result = await agent.answer(
                collection_name=collection,
                query=text,
                rag_service=rag,
                history=history,
                limit=settings.AGENT_RETRIEVAL_LIMIT,
                threshold=settings.AGENT_RETRIEVAL_THRESHOLD,
            )
            answer = result.text
            logger.info(
                "agent.doc_chat conv=%s used_retrieval=%s planner_query=%r hits=%d",
                conv.id,
                result.used_retrieval,
                result.planner_query,
                len(result.retrieved),
            )
        else:
            answer = await rag.answer(collection, text, limit=5, threshold=0.3)

        reply = Message(
            conversation_id=conv.id, role=MessageRole.DOC, text=answer or ""
        )
        await self._messages.add(reply)

        conv.updated_at = datetime.now(timezone.utc)

        return ChatReplyResponse(
            userMessage=_message_response(user_msg),
            reply=_message_response(reply),
        )

    # Convenience helper for the back-compat ``POST /chat/doc`` route —
    # creates a throwaway conversation, uploads nothing, just calls the LLM.
    async def legacy_doc_reply(
        self,
        owner: User,
        text: str,
        rag: RAGService,
        agent: Optional[AgentInterface] = None,
    ) -> str:
        collection = collection_for_conversation(f"adhoc_{owner.id}")
        if agent is not None:
            settings = get_settings()
            result = await agent.answer(
                collection_name=collection,
                query=text,
                rag_service=rag,
                history=None,
                limit=settings.AGENT_RETRIEVAL_LIMIT,
                threshold=settings.AGENT_RETRIEVAL_THRESHOLD,
            )
            return (
                result.text
                or "No indexed files are associated with this session."
            )
        answer = await rag.answer(collection, text, limit=3)
        return answer or "No indexed files are associated with this session."

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

    # ---------- helpers ----------

    async def _save_file(
        self, conv_id: str, upload: UploadFile
    ) -> tuple[DocumentFile, dict]:
        directory = doc_files_dir(conv_id)
        ext = ext_of(upload.filename or "")
        safe = clean_filename(Path(upload.filename or "file").stem) + ext
        storage = directory / f"{random_suffix(16)}_{safe}"
        settings = get_settings()
        max_bytes = settings.UPLOAD_DOC_MAX_MB * 1024 * 1024
        total = 0
        too_large = False
        async with aiofiles.open(storage, "wb") as fh:
            while True:
                data = await upload.read(settings.FILE_DEFAULT_CHUNK_SIZE)
                if not data:
                    break
                total += len(data)
                if total > max_bytes:
                    too_large = True
                    break
                await fh.write(data)
        # Unlink AFTER the handle is closed — Windows refuses to remove a file
        # while it is still open.
        if too_large:
            try:
                os.unlink(storage)
            except FileNotFoundError:
                pass
            raise APIError(
                ErrorCode.FILE_TOO_LARGE,
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                "File exceeds the maximum allowed size.",
            )
        if ext == ".pdf" and detect_pdf_encrypted(storage):
            os.unlink(storage)
            raise APIError(
                ErrorCode.FILE_ENCRYPTED,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Encrypted PDFs are not supported.",
            )
        record = DocumentFile(
            conversation_id=conv_id,
            name=upload.filename or "file",
            size_bytes=total,
            mime=(upload.content_type or "application/octet-stream").lower(),
            storage_path=str(storage),
            status=DocumentFileStatus.PROCESSING,
        )
        try:
            await self._files.add(record)
        except Exception:
            # Row failed to persist — remove the just-written file so it isn't
            # orphaned on disk.
            try:
                os.unlink(storage)
            except FileNotFoundError:
                pass
            raise
        job = {
            "file_id": record.id,
            "conversation_id": conv_id,
            "path": str(storage),
        }
        return record, job


def _conv_response(conv: Conversation, message_count: int) -> ConversationResponse:
    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        subjectId=conv.subject_id,
        createdAt=conv.created_at,
        updatedAt=conv.updated_at,
        messageCount=message_count,
    )


def _message_response(msg: Message) -> MessageResponse:
    return MessageResponse(
        id=msg.id,
        role=msg.role.value,
        text=msg.text,
        createdAt=msg.created_at,
    )


def _file_response(f: DocumentFile) -> DocumentFileResponse:
    return DocumentFileResponse(
        id=f.id,
        name=f.name,
        status=f.status.value,
        sizeBytes=f.size_bytes,
        mime=f.mime,
    )


async def index_doc_file_job(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    file_id: str,
    conversation_id: str,
    path: str,
    rag_service: RAGService,
) -> None:
    """Background task: index one doc-chat file and flip status to ready."""
    try:
        chunks = await asyncio.to_thread(ingest_file, Path(path))
        if chunks:
            await rag_service.index_chunks(
                collection_name=collection_for_conversation(conversation_id),
                chunks=chunks,
                do_reset=False,
                id_prefix=file_id,
            )
        async with session_factory() as session:
            async with session.begin():
                await DocumentFileRepository(session).set_status(
                    file_id, DocumentFileStatus.READY
                )
    except Exception:  # noqa: BLE001
        logger.exception("Indexing failed for doc file %s", file_id)
        # Surface the failure so the file doesn't stay stuck in PROCESSING.
        try:
            async with session_factory() as session:
                async with session.begin():
                    await DocumentFileRepository(session).set_status(
                        file_id, DocumentFileStatus.FAILED
                    )
        except Exception:  # noqa: BLE001
            logger.exception("Could not mark doc file %s as FAILED", file_id)
