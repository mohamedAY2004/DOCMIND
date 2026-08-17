from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ConversationKind, User, UserRole
from helpers.errors import APIError, ErrorCode
from repositories.conversation_repository import ConversationRepository
from repositories.document_file_repository import DocumentFileRepository
from repositories.material_repository import MaterialRepository
from repositories.message_repository import MessageRepository
from repositories.subject_repository import SubjectRepository
from schemas.citation import CitationViewResponse
from services.storage_service import get_storage


class CitationService:
    def __init__(self, session: AsyncSession) -> None:
        self._messages = MessageRepository(session)
        self._conversations = ConversationRepository(session)
        self._files = DocumentFileRepository(session)
        self._materials = MaterialRepository(session)
        self._subjects = SubjectRepository(session)

    async def view(self, caller: User, message_id: str, citation_id: str) -> CitationViewResponse:
        message = await self._messages.get(message_id)
        if message is None:
            raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Message not found.")
        citation = next((item for item in (message.citations or []) if item.get("id") == citation_id), None)
        if citation is None:
            raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Citation not found.")
        conversation = await self._conversations.get(message.conversation_id)
        if conversation is None:
            raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Conversation not found.")

        source_kind = citation.get("sourceKind")
        source_id = str(citation.get("sourceId") or "")
        if conversation.kind == ConversationKind.DOC:
            if conversation.owner_id != caller.id:
                raise APIError(ErrorCode.FORBIDDEN, status.HTTP_403_FORBIDDEN, "You do not own this document chat.")
            source = await self._files.get(source_id)
            if source is None or source.conversation_id != conversation.id:
                raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Source file not found.")
        else:
            subject_id = conversation.subject_id or ""
            if caller.role == UserRole.STUDENT:
                if conversation.owner_id != caller.id:
                    raise APIError(ErrorCode.FORBIDDEN, status.HTTP_403_FORBIDDEN, "You do not own this tutor conversation.")
                if not await self._subjects.is_student_of(subject_id, caller.id):
                    raise APIError(ErrorCode.FORBIDDEN, status.HTTP_403_FORBIDDEN, "You are not enrolled in this subject.")
            if caller.role == UserRole.INSTRUCTOR and not await self._subjects.is_instructor_of(subject_id, caller.id):
                raise APIError(ErrorCode.FORBIDDEN, status.HTTP_403_FORBIDDEN, "You are not assigned to this subject.")
            source = await self._materials.get(source_id)
            if source is None or source.subject_id != subject_id:
                raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Source material not found.")

        location = citation.get("location") or {}
        url = get_storage().inline_url(
            backend=getattr(source, "storage_backend", "local"),
            key=getattr(source, "storage_key", None),
            source_kind=source_kind,
            source_id=source.id,
            filename=source.name,
        )
        return CitationViewResponse(
            url=url,
            expiresAt=datetime.now(timezone.utc) + timedelta(seconds=60),
            sourceName=source.name,
            locationType=str(location.get("type") or "chunk"),
            locationNumber=int(location.get("number") or 1),
            section=citation.get("section"),
            excerpt=str(citation.get("excerpt") or ""),
        )

    async def local_content(self, token: str) -> tuple[str, str]:
        try:
            kind, source_id = get_storage().verify_local_token(token)
        except ValueError as exc:
            raise APIError(ErrorCode.UNAUTHENTICATED, status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
        source = await self._files.get(source_id) if kind == "document_file" else await self._materials.get(source_id)
        if source is None or not source.storage_path or not Path(source.storage_path).is_file():
            raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Citation file is no longer available.")
        return source.storage_path, source.mime
