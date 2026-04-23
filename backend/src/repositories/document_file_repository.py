"""Data access for :class:`DocumentFile`."""
from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import func, select, update

from db.models import DocumentFile, DocumentFileStatus

from .base import BaseRepository


class DocumentFileRepository(BaseRepository[DocumentFile]):
    model = DocumentFile

    async def get(self, file_id: str) -> Optional[DocumentFile]:
        return await self.session.get(DocumentFile, file_id)

    async def list_for_conversation(self, conv_id: str) -> Sequence[DocumentFile]:
        result = await self.session.execute(
            select(DocumentFile)
            .where(DocumentFile.conversation_id == conv_id)
            .order_by(DocumentFile.created_at)
        )
        return result.scalars().all()

    async def count_for_conversation(self, conv_id: str) -> int:
        result = await self.session.execute(
            select(func.count(DocumentFile.id)).where(
                DocumentFile.conversation_id == conv_id
            )
        )
        return int(result.scalar() or 0)

    async def count_still_processing(self, conv_id: str) -> int:
        result = await self.session.execute(
            select(func.count(DocumentFile.id)).where(
                DocumentFile.conversation_id == conv_id,
                DocumentFile.status == DocumentFileStatus.PROCESSING,
            )
        )
        return int(result.scalar() or 0)

    async def add(self, f: DocumentFile) -> DocumentFile:
        self.session.add(f)
        await self.session.flush()
        return f

    async def set_status(self, file_id: str, status: DocumentFileStatus) -> None:
        await self.session.execute(
            update(DocumentFile).where(DocumentFile.id == file_id).values(status=status)
        )
