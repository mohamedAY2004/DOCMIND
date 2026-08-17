"""Document chat business logic (spec §8.2)."""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator, List, Optional, Sequence

import aiofiles
from fastapi import UploadFile, status
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from db.models import (
    Conversation,
    ConversationKind,
    DocumentFile,
    DocumentFileStatus,
    GenerationStatus,
    GroundingStatus,
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
from services.answer_result import AnswerResult, result_from_generation
from services.ephemeral_store import EphemeralStore
from services.generation_control import (
    GenerationCancelled,
    await_cancellable,
    iter_cancellable,
)
from services.storage_service import get_storage
from services.retention_service import document_expiry_for_current_term
from services.telemetry_service import TelemetryService
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
        conv.expires_at = await document_expiry_for_current_term(
            self._session, datetime.now(timezone.utc)
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
        await get_storage().delete(
            backend=target.storage_backend,
            key=target.storage_key,
            local_path=target.storage_path,
        )

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
            await get_storage().delete(
                backend=f.storage_backend,
                key=f.storage_key,
                local_path=f.storage_path,
            )
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
            answer_result = result_from_generation(
                result.text or "", result.retrieved, source_kind="document_file"
            ) if result.retrieved else AnswerResult(
                text=result.text or "",
                grounding_status="no_context" if result.used_retrieval else "ungrounded",
            )
            logger.info(
                "agent.doc_chat conv=%s used_retrieval=%s planner_query=%r hits=%d",
                conv.id,
                result.used_retrieval,
                result.planner_query,
                len(result.retrieved),
            )
        else:
            answer_result = await rag.answer(collection, text, limit=5, threshold=0.3)

        reply = Message(
            conversation_id=conv.id,
            role=MessageRole.DOC,
            text=answer_result.text,
            citations=answer_result.citations,
            grounding_status=GroundingStatus(answer_result.grounding_status),
        )
        await self._messages.add(reply)
        await TelemetryService(self._session).record(
            message_id=reply.id, subject_id=None, result=answer_result, state="complete"
        )

        conv.updated_at = datetime.now(timezone.utc)

        return ChatReplyResponse(
            userMessage=_message_response(user_msg),
            reply=_message_response(reply),
        )

    async def stream_message(
        self,
        owner: User,
        conv_id: str,
        text: str,
        rag: RAGService,
        agent: Optional[AgentInterface],
        store: EphemeralStore,
    ) -> AsyncIterator[tuple[str, dict]]:
        """Validate before headers are sent, then return the event iterator."""
        conv = await self._load_owned(owner, conv_id)
        if await self._files.count_still_processing(conv.id) > 0:
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

        history_turns = get_settings().AGENT_HISTORY_TURNS
        history = (
            await self._recent_history(conv.id, history_turns)
            if agent is not None and history_turns > 0
            else None
        )
        return self._stream_prepared(conv, text, rag, agent, store, history)

    async def _stream_prepared(
        self,
        conv: Conversation,
        text: str,
        rag: RAGService,
        agent: Optional[AgentInterface],
        store: EphemeralStore,
        history: Optional[list[dict]],
    ) -> AsyncIterator[tuple[str, dict]]:
        """Persist a draft reply, then forward provider deltas to the client."""

        user_msg = await self._messages.add(
            Message(conversation_id=conv.id, role=MessageRole.USER, text=text)
        )
        reply = await self._messages.add(
            Message(
                conversation_id=conv.id,
                role=MessageRole.DOC,
                text="",
                generation_status=GenerationStatus.GENERATING,
            )
        )
        conv.updated_at = datetime.now(timezone.utc)
        await self._session.commit()
        yield "message.created", {
            "userMessage": _message_response(user_msg).model_dump(mode="json"),
            "reply": _message_response(reply).model_dump(mode="json"),
        }

        result: AnswerResult | None = None
        try:
            collection = collection_for_conversation(conv.id)
            if agent is not None:
                settings = get_settings()
                agent_kwargs = {
                    "collection_name": collection,
                    "query": text,
                    "rag_service": rag,
                    "history": history,
                    "limit": settings.AGENT_RETRIEVAL_LIMIT,
                    "threshold": settings.AGENT_RETRIEVAL_THRESHOLD,
                }
                if hasattr(agent, "answer_stream"):
                    agent_result = None
                    source = agent.answer_stream(**agent_kwargs)
                    async for kind, payload in iter_cancellable(
                        source, store=store, reply_id=reply.id
                    ):
                        if kind == "delta":
                            yield "answer.delta", {
                                "replyId": reply.id,
                                "delta": payload,
                            }
                        else:
                            agent_result = payload
                    if agent_result is None:
                        raise RuntimeError("Agent completed without a result")
                else:
                    agent_result = await await_cancellable(
                        agent.answer(**agent_kwargs),
                        store=store,
                        reply_id=reply.id,
                    )
                result = (
                    result_from_generation(
                        agent_result.text or "",
                        agent_result.retrieved,
                        source_kind="document_file",
                    )
                    if agent_result.retrieved
                    else AnswerResult(
                        text=agent_result.text or "",
                        grounding_status=(
                            "no_context" if agent_result.used_retrieval else "ungrounded"
                        ),
                    )
                )
                if not hasattr(agent, "answer_stream") and result.text:
                    yield "answer.delta", {"replyId": reply.id, "delta": result.text}
            else:
                source = rag.answer_stream(collection, text, limit=5, threshold=0.3)
                async for kind, payload in iter_cancellable(
                    source, store=store, reply_id=reply.id
                ):
                    if kind == "delta":
                        yield "answer.delta", {"replyId": reply.id, "delta": payload}
                    else:
                        result = payload

            if result is None:
                raise RuntimeError("Generation completed without a result")
            completed = await self._messages.complete_if_generating(
                reply.id,
                text=result.text,
                citations=result.citations,
                grounding_status=GroundingStatus(result.grounding_status),
            )
            if not completed:
                await self._session.refresh(reply)
                await self._session.commit()
                yield "answer.completed", {
                    "reply": _message_response(reply).model_dump(mode="json")
                }
                return
            reply.text = result.text
            reply.citations = result.citations
            reply.grounding_status = GroundingStatus(result.grounding_status)
            reply.generation_status = GenerationStatus.COMPLETE
            await TelemetryService(self._session).record(
                message_id=reply.id, subject_id=None, result=result, state="complete"
            )
            await self._session.commit()
            yield "answer.citations", {
                "replyId": reply.id,
                "citations": result.citations,
                "groundingStatus": result.grounding_status,
            }
            yield "answer.completed", {
                "reply": _message_response(reply).model_dump(mode="json")
            }
        except GenerationCancelled:
            await self._messages.cancel_if_generating(reply.id)
            await self._session.refresh(reply)
            await self._session.commit()
            yield "answer.completed", {
                "reply": _message_response(reply).model_dump(mode="json")
            }
        except asyncio.CancelledError:
            await self._messages.cancel_if_generating(reply.id)
            await self._session.commit()
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Document answer stream failed reply=%s", reply.id)
            failed = await self._messages.fail_if_generating(reply.id)
            if not failed:
                await self._session.refresh(reply)
                await self._session.commit()
                yield "answer.completed", {
                    "reply": _message_response(reply).model_dump(mode="json")
                }
                return
            reply.generation_status = GenerationStatus.FAILED
            await TelemetryService(self._session).record(
                message_id=reply.id, subject_id=None, state="failed", error_code="GENERATION_FAILED"
            )
            await self._session.commit()
            yield "answer.failed", {
                "replyId": reply.id,
                "code": "GENERATION_FAILED",
                "message": str(exc),
            }

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
        return answer.text or "No indexed files are associated with this session."

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
        storage_backend = settings.STORAGE_BACKEND
        storage_key = str(storage)
        if storage_backend == "s3":
            storage_key = f"document-files/{conv_id}/{random_suffix(24)}{ext}"
            try:
                await get_storage().upload(
                    str(storage), storage_key,
                    (upload.content_type or "application/octet-stream").lower(),
                )
            except Exception:
                try:
                    os.unlink(storage)
                except FileNotFoundError:
                    pass
                raise
        record = DocumentFile(
            conversation_id=conv_id,
            name=upload.filename or "file",
            size_bytes=total,
            mime=(upload.content_type or "application/octet-stream").lower(),
            storage_path=str(storage),
            storage_key=storage_key,
            storage_backend=storage_backend,
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
            if storage_backend == "s3":
                await get_storage().delete(
                    backend="s3", key=storage_key, local_path=None
                )
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
        citations=msg.citations or [],
        generationStatus=msg.generation_status.value,
        groundingStatus=msg.grounding_status.value if msg.grounding_status else None,
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
                record = await DocumentFileRepository(session).get(file_id)
        if record and record.storage_backend == "s3":
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass
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
