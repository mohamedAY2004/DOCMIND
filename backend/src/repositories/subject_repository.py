"""Data access for :class:`Subject` and its instructor roster."""
from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import delete, select

from db.models import (
    InstructorSubjectRole,
    Subject,
    SubjectInstructor,
    SubjectStudent,
    User,
    UserRole,
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

    async def instructors_detailed(self, subject_id: str) -> Sequence[User]:
        stmt = (
            select(User)
            .join(SubjectInstructor, SubjectInstructor.user_id == User.id)
            .where(
                SubjectInstructor.subject_id == subject_id,
                User.role == UserRole.INSTRUCTOR,
            )
            .order_by(User.name)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

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
        stmt = (
            select(User)
            .join(SubjectInstructor, SubjectInstructor.user_id == User.id)
            .where(
                SubjectInstructor.subject_id == subject_id,
                SubjectInstructor.instructor_role == InstructorSubjectRole.SUPER,
            )
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
        stmt = (
            select(Subject)
            .join(SubjectStudent, SubjectStudent.subject_id == Subject.id)
            .where(SubjectStudent.user_id == user_id)
            .order_by(Subject.title)
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
