"""Message ORM model (spec §8.1)."""
from __future__ import annotations

import enum
import uuid
from typing import Any, Optional

from sqlalchemy import BigInteger, ForeignKey, Sequence, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin, pg_enum


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"  # tutor-chat AI reply
    DOC = "doc"  # document-chat AI reply


class GenerationStatus(str, enum.Enum):
    GENERATING = "generating"
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    FAILED = "failed"


class GroundingStatus(str, enum.Enum):
    GROUNDED = "grounded"
    PARTIALLY_GROUNDED = "partially_grounded"
    UNGROUNDED = "ungrounded"
    NO_CONTEXT = "no_context"


def _new_message_id() -> str:
    return "msg_" + uuid.uuid4().hex[:20]


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_new_message_id)
    sort_id: Mapped[int] = mapped_column(
        BigInteger,
        Sequence("message_sort_id_seq"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[MessageRole] = mapped_column(
        pg_enum(MessageRole, name="message_role"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    generation_status: Mapped[GenerationStatus] = mapped_column(
        pg_enum(GenerationStatus, name="generation_status"),
        nullable=False,
        default=GenerationStatus.COMPLETE,
    )
    grounding_status: Mapped[Optional[GroundingStatus]] = mapped_column(
        pg_enum(GroundingStatus, name="grounding_status"), nullable=True
    )
