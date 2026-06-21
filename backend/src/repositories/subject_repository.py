"""Data access for :class:`Subject` and its instructor roster."""
from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import delete, nulls_last, select

from db.models import (
    InstructorSubjectRole,
    Semester,
    SemesterState,
    Subject,
    SubjectInstructor,
    SubjectStudent,
    User,
    UserRole,
    derive_semester_state,
)

from .base import BaseRepository


class SubjectRepository(BaseRepository[Subject]):
    model = Subject

    async def get(self, subject_id: str) -> Optional[Subject]:
        return await self.session.get(Subject, subject_id)

    async def list_all(self) -> Sequence[Subject]:
        result = await self.session.execute(select(Subject).order_by(Subject.title))
        return result.scalars().all()

    async def list_paginated(
        self,
        *,
        search: Optional[str] = None,
        semester_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Subject], int]:
        from sqlalchemy import func, or_

        where = []
        if search:
            like = f"%{search.lower()}%"
            where.append(
                or_(
                    func.lower(Subject.title).like(like),
                    func.lower(Subject.course_code).like(like),
                    func.lower(Subject.id).like(like),
                )
            )
        if semester_id:
            where.append(Subject.semester_id == semester_id)

        base = select(Subject)
        count_stmt = select(func.count()).select_from(Subject)
        if where:
            base = base.where(*where)
            count_stmt = count_stmt.where(*where)

        total = int((await self.session.execute(count_stmt)).scalar() or 0)
        rows = (
            await self.session.execute(
                base.order_by(Subject.title).offset(offset).limit(limit)
            )
        ).scalars().all()
        return rows, total

    async def list_for_instructor(self, user_id: str) -> Sequence[Subject]:
        stmt = (
            select(Subject)
            .join(SubjectInstructor, SubjectInstructor.subject_id == Subject.id)
            .where(SubjectInstructor.user_id == user_id)
            .order_by(Subject.title)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def instructor_ids(self, subject_id: str) -> list[str]:
        stmt = select(SubjectInstructor.user_id).where(
            SubjectInstructor.subject_id == subject_id
        )
        result = await self.session.execute(stmt)
        return [row for row in result.scalars().all()]

    async def instructors_with_roles(
        self, subject_id: str
    ) -> Sequence[tuple[User, InstructorSubjectRole]]:
        """Return each instructor alongside their per-subject role."""
        stmt = (
            select(User, SubjectInstructor.instructor_role)
            .join(SubjectInstructor, SubjectInstructor.user_id == User.id)
            .where(
                SubjectInstructor.subject_id == subject_id,
                User.role == UserRole.INSTRUCTOR,
            )
            .order_by(User.name)
        )
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def get_super_instructor(self, subject_id: str) -> Optional[User]:
        # The partial unique index (uq_subject_one_super) guarantees at most one
        # super per subject; order + limit defensively so a legacy double-super
        # still resolves deterministically.
        stmt = (
            select(User)
            .join(SubjectInstructor, SubjectInstructor.user_id == User.id)
            .where(
                SubjectInstructor.subject_id == subject_id,
                SubjectInstructor.instructor_role == InstructorSubjectRole.SUPER,
            )
            .order_by(User.id)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_instructor_role(
        self, subject_id: str, user_id: str
    ) -> Optional[InstructorSubjectRole]:
        stmt = select(SubjectInstructor.instructor_role).where(
            SubjectInstructor.subject_id == subject_id,
            SubjectInstructor.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar()

    async def is_instructor_of(self, subject_id: str, user_id: str) -> bool:
        stmt = select(SubjectInstructor).where(
            SubjectInstructor.subject_id == subject_id,
            SubjectInstructor.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.first() is not None

    async def add(self, subject: Subject) -> Subject:
        self.session.add(subject)
        await self.session.flush()
        return subject

    async def replace_instructors(
        self,
        subject_id: str,
        instructor_ids: Sequence[str],
        super_instructor_id: str,
    ) -> None:
        await self.session.execute(
            delete(SubjectInstructor).where(SubjectInstructor.subject_id == subject_id)
        )
        for user_id in set(instructor_ids):
            role = (
                InstructorSubjectRole.SUPER
                if user_id == super_instructor_id
                else InstructorSubjectRole.VIEWER
            )
            self.session.add(
                SubjectInstructor(
                    subject_id=subject_id,
                    user_id=user_id,
                    instructor_role=role,
                )
            )
        await self.session.flush()

    # ---------------- student roster ----------------

    async def list_for_student(self, user_id: str) -> Sequence[Subject]:
        # Latest semester first: the student's most recent term surfaces on top
        # of "Chat with Tutors", older (archived) terms below. ``sort_order`` and
        # ``start_date`` agree by construction (the seeder increments sort_order
        # chronologically), so either alone orders correctly; start_date is the
        # primary key for true chronology and sort_order the admin-set tiebreaker.
        # An outer join keeps subjects with no semester (NULL dates) — they sort
        # last via ``nulls_last`` and fall back to alphabetical by title.
        stmt = (
            select(Subject)
            .join(SubjectStudent, SubjectStudent.subject_id == Subject.id)
            .outerjoin(Semester, Semester.id == Subject.semester_id)
            .where(SubjectStudent.user_id == user_id)
            .order_by(
                nulls_last(Semester.start_date.desc()),
                nulls_last(Semester.sort_order.desc()),
                Subject.title.asc(),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def student_ids(self, subject_id: str) -> list[str]:
        stmt = select(SubjectStudent.user_id).where(
            SubjectStudent.subject_id == subject_id
        )
        result = await self.session.execute(stmt)
        return [row for row in result.scalars().all()]

    async def student_count(self, subject_id: str) -> int:
        from sqlalchemy import func

        stmt = select(func.count()).select_from(SubjectStudent).where(
            SubjectStudent.subject_id == subject_id
        )
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def students_detailed(self, subject_id: str) -> Sequence[User]:
        stmt = (
            select(User)
            .join(SubjectStudent, SubjectStudent.user_id == User.id)
            .where(
                SubjectStudent.subject_id == subject_id,
                User.role == UserRole.STUDENT,
            )
            .order_by(User.name)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def is_student_of(self, subject_id: str, user_id: str) -> bool:
        stmt = select(SubjectStudent).where(
            SubjectStudent.subject_id == subject_id,
            SubjectStudent.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.first() is not None

    async def replace_students(
        self, subject_id: str, student_ids: Sequence[str]
    ) -> None:
        await self.session.execute(
            delete(SubjectStudent).where(SubjectStudent.subject_id == subject_id)
        )
        for user_id in set(student_ids):
            self.session.add(
                SubjectStudent(subject_id=subject_id, user_id=user_id)
            )
        await self.session.flush()

    async def subject_ids_for_student(self, user_id: str) -> list[str]:
        stmt = select(SubjectStudent.subject_id).where(
            SubjectStudent.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return [row for row in result.scalars().all()]

    async def replace_subjects_for_student(
        self, user_id: str, subject_ids: Sequence[str]
    ) -> None:
        await self.session.execute(
            delete(SubjectStudent).where(SubjectStudent.user_id == user_id)
        )
        for sid in set(subject_ids):
            self.session.add(SubjectStudent(subject_id=sid, user_id=user_id))
        await self.session.flush()

    async def has_active_conversations(self, subject_id: str) -> bool:
        """Cascade guard used by ``DELETE /admin/subjects/:id`` (spec §6.7)."""
        from db.models import Conversation

        stmt = select(Conversation.id).where(Conversation.subject_id == subject_id)
        result = await self.session.execute(stmt.limit(1))
        return result.first() is not None

    async def semester_state_for_subject(self, subject_id: str) -> SemesterState:
        """Derived lifecycle state of the subject's semester (Tier 2A gate).

        A subject with no semester (``semester_id IS NULL``), a dangling
        semester, or a semester with no date window resolves to ``ACTIVE`` —
        the fail-open rule from :func:`derive_semester_state` — so only a
        genuinely past/future term ever restricts new tutor turns.
        """
        stmt = (
            select(Semester.start_date, Semester.end_date)
            .join(Subject, Subject.semester_id == Semester.id)
            .where(Subject.id == subject_id)
        )
        row = (await self.session.execute(stmt)).first()
        if row is None:
            return SemesterState.ACTIVE
        return derive_semester_state(row[0], row[1])
