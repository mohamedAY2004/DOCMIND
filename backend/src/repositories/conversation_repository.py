"""Data access for :class:`Conversation`."""
from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import func, select

from db.models import Conversation, ConversationKind, Message

from .base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    model = Conversation

    async def get(self, conv_id: str) -> Optional[Conversation]:
        return await self.session.get(Conversation, conv_id)

    async def list_for_owner(
        self,
        *,
        owner_id: str,
        kind: ConversationKind,
        subject_id: Optional[str],
        offset: int,
        limit: int,
    ) -> tuple[Sequence[Conversation], int]:
        stmt = select(Conversation).where(
            Conversation.owner_id == owner_id,
            Conversation.kind == kind,
        )
        if subject_id is not None:
            stmt = stmt.where(Conversation.subject_id == subject_id)

        count_stmt = stmt.with_only_columns(func.count(Conversation.id)).order_by(None)
        total = int((await self.session.execute(count_stmt)).scalar() or 0)

        rows = (
            await self.session.execute(
                stmt.order_by(Conversation.updated_at.desc()).offset(offset).limit(limit)
            )
        ).scalars().all()
        return rows, total

    async def count_for_owner(
        self,
        *,
        owner_id: str,
        kind: ConversationKind,
        subject_id: Optional[str] = None,
    ) -> int:
        stmt = select(func.count(Conversation.id)).where(
            Conversation.owner_id == owner_id,
            Conversation.kind == kind,
        )
        if subject_id is not None:
            stmt = stmt.where(Conversation.subject_id == subject_id)
        return int((await self.session.execute(stmt)).scalar() or 0)

    async def add(self, conv: Conversation) -> Conversation:
        self.session.add(conv)
        await self.session.flush()
        return conv

    async def message_count(self, conv_id: str) -> int:
        result = await self.session.execute(
            select(func.count(Message.id)).where(Message.conversation_id == conv_id)
        )
        return int(result.scalar() or 0)

    async def message_counts(self, conv_ids: list[str]) -> dict[str, int]:
        """Return ``{conversation_id: count}`` for all given IDs in one query."""
        if not conv_ids:
            return {}
        stmt = (
            select(Message.conversation_id, func.count(Message.id))
            .where(Message.conversation_id.in_(conv_ids))
            .group_by(Message.conversation_id)
        )
        rows = (await self.session.execute(stmt)).all()
        return {row[0]: row[1] for row in rows}
