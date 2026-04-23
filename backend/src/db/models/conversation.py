"""Conversation ORM model (spec §8.1). Covers both document and tutor chat."""
from __future__ import annotations

import enum
import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin, pg_enum


class ConversationKind(str, enum.Enum):
    DOC = "doc"
    TUTOR = "tutor"


def _new_conv_id() -> str:
    return "conv_" + uuid.uuid4().hex[:16]


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_new_conv_id)
    owner_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[ConversationKind] = mapped_column(
        pg_enum(ConversationKind, name="conversation_kind"), nullable=False
    )
    subject_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False, default="New Chat")
