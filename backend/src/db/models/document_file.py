"""DocumentFile ORM model (spec §8.2.1). Files attached to a doc-chat conversation."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin, pg_enum


class DocumentFileStatus(str, enum.Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


def _new_file_id() -> str:
    return "f_" + uuid.uuid4().hex[:16]


class DocumentFile(Base, TimestampMixin):
    __tablename__ = "document_files"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_new_file_id)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime: Mapped[str] = mapped_column(String(120), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[DocumentFileStatus] = mapped_column(
        pg_enum(DocumentFileStatus, name="document_file_status"),
        nullable=False,
        default=DocumentFileStatus.PROCESSING,
    )
