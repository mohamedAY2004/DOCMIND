"""Association table linking subjects to their instructor roster (spec §6)."""
from __future__ import annotations

import enum

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, pg_enum


class InstructorSubjectRole(str, enum.Enum):
    SUPER = "super"
    VIEWER = "viewer"


class SubjectInstructor(Base):
    __tablename__ = "subject_instructors"

    # Partial unique index: at most one 'super' instructor per subject. Created in
    # migration 0004_one_super_per_subject; declared here for autogenerate parity.
    __table_args__ = (
        Index(
            "uq_subject_one_super",
            "subject_id",
            unique=True,
            postgresql_where=text("instructor_role = 'super'"),
        ),
    )

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
