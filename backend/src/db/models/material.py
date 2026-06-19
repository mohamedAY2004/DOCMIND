"""Material ORM model (spec §7.1). A subject-scoped uploaded file."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin, pg_enum


class MaterialStatus(str, enum.Enum):
    INDEXING = "indexing"
    PROCESSED = "processed"
    FAILED = "failed"


def _new_material_id() -> str:
    return "M-" + uuid.uuid4().hex[:12].upper()


class Material(Base, TimestampMixin):
    __tablename__ = "materials"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_material_id)
    subject_id: Mapped[str] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime: Mapped[str] = mapped_column(String(120), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[MaterialStatus] = mapped_column(
        pg_enum(MaterialStatus, name="material_status"),
        nullable=False,
        default=MaterialStatus.INDEXING,
    )
    uploaded_by_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
