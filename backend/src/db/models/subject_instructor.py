"""Association table linking subjects to their instructor roster (spec §6)."""
from __future__ import annotations

import enum

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, pg_enum


class InstructorSubjectRole(str, enum.Enum):
    SUPER = "super"
    VIEWER = "viewer"


class SubjectInstructor(Base):
    __tablename__ = "subject_instructors"

    subject_id: Mapped[str] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    instructor_role: Mapped[InstructorSubjectRole] = mapped_column(
        pg_enum(InstructorSubjectRole, name="instructor_subject_role"),
        nullable=False,
        default=InstructorSubjectRole.VIEWER,
    )
