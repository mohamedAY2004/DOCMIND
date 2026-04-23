"""Subject ORM model (spec §6.1). ``id`` is the slug."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # slug
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    course_code: Mapped[str] = mapped_column(String(80), nullable=False)
    semester_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("semesters.id", ondelete="SET NULL"), nullable=True
    )
