"""Message ORM model (spec §8.1)."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin, pg_enum


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"  # tutor-chat AI reply
    DOC = "doc"  # document-chat AI reply


def _new_message_id() -> str:
    return "msg_" + uuid.uuid4().hex[:20]


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_new_message_id)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[MessageRole] = mapped_column(
        pg_enum(MessageRole, name="message_role"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
