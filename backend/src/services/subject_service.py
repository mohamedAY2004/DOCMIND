"""Subject business logic (spec §6)."""
from __future__ import annotations

from typing import List, Optional

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Subject, User, UserRole
from helpers.errors import APIError, ErrorCode
from repositories.activity_repository import ActivityRepository
from repositories.material_repository import MaterialRepository
from repositories.semester_repository import SemesterRepository
from repositories.subject_repository import SubjectRepository
from repositories.user_repository import UserRepository
from schemas.subject import (
    CreateSubjectRequest,
    InstructorResponse,
    StudentResponse,
    SubjectResponse,
    UpdateSubjectRequest,
)
from services.activity_logger import ActivityLogger


class SubjectService:
    def __init__(self, session: AsyncSession) -> None:
        self._subjects = SubjectRepository(session)
        self._materials = MaterialRepository(session)
        self._users = UserRepository(session)
        self._semesters = SemesterRepository(session)
        self._activity = ActivityLogger(ActivityRepository(session))

    async def _to_response(self, subject: Subject) -> SubjectResponse:
        count = await self._materials.count_for_subject(subject.id)
        instructor_ids = await self._subjects.instructor_ids(subject.id)
        student_ids = await self._subjects.student_ids(subject.id)
        super_instructor = await self._subjects.get_super_instructor(subject.id)
        semester_state = await self._subjects.semester_state_for_subject(subject.id)
        return SubjectResponse(
            id=subject.id,
            title=subject.title,
            description=subject.description,
            courseCode=subject.course_code,
            semesterId=subject.semester_id,
            pdfCount=_format_pdf_count(count),
            instructorIds=instructor_ids,
            superInstructorId=super_instructor.id if super_instructor else None,
            studentIds=student_ids,
            studentCount=len(student_ids),
            semesterState=semester_state.value,
        )

    async def list_all(self) -> List[SubjectResponse]:
        return [await self._to_response(s) for s in await self._subjects.list_all()]

    async def list_paginated(
        self,
        *,
        search: Optional[str] = None,
        semester_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[SubjectResponse], int]:
        rows, total = await self._subjects.list_paginated(
            search=search, semester_id=semester_id, offset=offset, limit=limit
        )
        items = [await self._to_response(s) for s in rows]
        return items, total

    async def list_for_student(self, student: User) -> List[SubjectResponse]:
        rows = await self._subjects.list_for_student(student.id)
        return [await self._to_response(s) for s in rows]

    async def list_for_instructor(
        self, caller: User, requested_id: Optional[str]
    ) -> List[SubjectResponse]:
        target_id = requested_id or caller.id
        if caller.role == UserRole.INSTRUCTOR and target_id != caller.id:
            raise APIError(
                ErrorCode.FORBIDDEN,
                status.HTTP_403_FORBIDDEN,
                "Instructors can only query their own subjects.",
            )
        rows = await self._subjects.list_for_instructor(target_id)
        return [await self._to_response(s) for s in rows]

    async def get(self, subject_id: str) -> SubjectResponse:
        subject = await self._subjects.get(subject_id)
        if subject is None:
            raise APIError(
                ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Subject not found."
            )
        return await self._to_response(subject)

    async def get_or_404(self, subject_id: str) -> Subject:
        subject = await self._subjects.get(subject_id)
        if subject is None:
            raise APIError(
                ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Subject not found."
            )
        return subject

    async def list_instructors(self, subject_id: str) -> List[InstructorResponse]:
        await self.get_or_404(subject_id)
        rows = await self._subjects.instructors_with_roles(subject_id)
        return [
            InstructorResponse(
                id=u.id,
                username=u.username,
                name=u.name,
                email=u.email,
                instructorRole=role.value,
            )
            for u, role in rows
        ]

    async def list_students(self, subject_id: str) -> List[StudentResponse]:
        await self.get_or_404(subject_id)
        rows = await self._subjects.students_detailed(subject_id)
        return [
            StudentResponse(id=u.id, name=u.name, email=u.email) for u in rows
        ]

    async def is_instructor_of(self, subject_id: str, user_id: str) -> bool:
        return await self._subjects.is_instructor_of(subject_id, user_id)

    async def is_student_of(self, subject_id: str, user_id: str) -> bool:
        return await self._subjects.is_student_of(subject_id, user_id)

    # ---------------- admin writes (spec §6.7) ----------------

    async def create(self, actor: User, body: CreateSubjectRequest) -> SubjectResponse:
        if await self._subjects.get(body.id) is not None:
            raise APIError(
                ErrorCode.CONFLICT,
                status.HTTP_409_CONFLICT,
                f"Subject '{body.id}' already exists.",
            )
        await self._validate_instructor_ids(body.instructorIds)
        await self._validate_student_ids(body.studentIds)
        super_id = await self._resolve_super_instructor_id(
            body.instructorIds, body.superInstructorId
        )
        subject = Subject(
            id=body.id,
            title=body.title,
            description=body.description,
            course_code=body.courseCode,
            semester_id=body.semesterId,
        )
        await self._subjects.add(subject)
        await self._subjects.replace_instructors(subject.id, body.instructorIds, super_id)
        await self._subjects.replace_students(subject.id, body.studentIds)
        await self._activity.record(
            action="Subject created", actor=actor, subject_label=subject.title
        )
        return await self._to_response(subject)

    async def update(
        self, actor: User, subject_id: str, body: UpdateSubjectRequest
    ) -> SubjectResponse:
        subject = await self.get_or_404(subject_id)
        if body.title is not None:
            subject.title = body.title
        if body.description is not None:
            subject.description = body.description
        if body.courseCode is not None:
            subject.course_code = body.courseCode
        if body.semesterId is not None:
            subject.semester_id = body.semesterId
        if body.instructorIds is not None:
            await self._validate_instructor_ids(body.instructorIds)
            # Determine super: use provided superInstructorId, or preserve the
            # existing super if they are still in the new roster, else default
            # to the first id in the list.
            current_super = await self._subjects.get_super_instructor(subject_id)
            current_super_id = current_super.id if current_super else None
            super_id = await self._resolve_super_instructor_id(
                body.instructorIds,
                body.superInstructorId or current_super_id,
            )
            await self._subjects.replace_instructors(subject.id, body.instructorIds, super_id)
        if body.studentIds is not None:
            await self._validate_student_ids(body.studentIds)
            await self._subjects.replace_students(subject.id, body.studentIds)
        await self._activity.record(
            action="Subject updated", actor=actor, subject_label=subject.title
        )
        return await self._to_response(subject)

    async def delete(self, actor: User, subject_id: str) -> None:
        subject = await self.get_or_404(subject_id)
        # Deliberately block on *any* conversation (not just "active" ones):
        # deleting the subject would cascade away its chat history, so we refuse
        # while any conversation still references it.
        if await self._subjects.has_active_conversations(subject_id):
            raise APIError(
                ErrorCode.CONFLICT,
                status.HTTP_409_CONFLICT,
                "Subject has conversations and cannot be deleted; remove them first.",
            )
        await self._activity.record(
            action="Subject deleted", actor=actor, subject_label=subject.title
        )
        # Rely on DB cascade for materials / subject_instructors.
        await self._subjects.delete(subject)

    async def _resolve_super_instructor_id(
        self, instructor_ids: List[str], preferred_super_id: Optional[str]
    ) -> str:
        """Return the user_id that should receive the SUPER role.

        Rules:
        - If ``preferred_super_id`` is provided and is in the roster → use it.
        - If ``preferred_super_id`` is provided but NOT in the roster → raise.
        - If ``preferred_super_id`` is None and the roster is non-empty → first id.
        - If the roster is empty → raise (a subject must have a super if it has instructors).
        """
        if not instructor_ids:
            # No instructors — there's no one to be super. A caller that still
            # supplied a superInstructorId is contradicting itself; reject it
            # instead of silently dropping the value.
            if preferred_super_id:
                raise APIError(
                    ErrorCode.VALIDATION_ERROR,
                    status.HTTP_400_BAD_REQUEST,
                    "superInstructorId must be one of the assigned instructors.",
                )
            return ""
        if preferred_super_id:
            if preferred_super_id not in instructor_ids:
                raise APIError(
                    ErrorCode.VALIDATION_ERROR,
                    status.HTTP_400_BAD_REQUEST,
                    "superInstructorId must be one of the assigned instructors.",
                )
            return preferred_super_id
        # Default: first entry in the list.
        return instructor_ids[0]

    async def _validate_instructor_ids(self, ids: List[str]) -> None:
        await self._validate_role_ids(
            ids, UserRole.INSTRUCTOR, "instructor", "invalid_instructor_ids"
        )

    async def _validate_student_ids(self, ids: List[str]) -> None:
        await self._validate_role_ids(
            ids, UserRole.STUDENT, "student", "invalid_student_ids"
        )

    async def _validate_role_ids(
        self, ids: List[str], expected: UserRole, label: str, detail_key: str
    ) -> None:
        """Validate that every id is an existing user with role ``expected``.

        Distinguishes ids that don't exist from ids that exist but have the
        wrong role, so the admin sees an accurate reason instead of a blanket
        "invalid".
        """
        if not ids:
            return
        found = await self._users.list_by_ids(ids)
        by_id = {u.id: u for u in found}
        not_found = [uid for uid in ids if uid not in by_id]
        wrong_role = [uid for uid in ids if uid in by_id and by_id[uid].role != expected]
        if not_found or wrong_role:
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                status.HTTP_400_BAD_REQUEST,
                f"One or more {label} ids are invalid.",
                details={detail_key: not_found, "wrong_role_ids": wrong_role},
            )

    async def _validate_subject_ids_exist(self, ids: List[str]) -> None:
        if not ids:
            return
        missing: List[str] = []
        for sid in ids:
            if await self._subjects.get(sid) is None:
                missing.append(sid)
        if missing:
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                status.HTTP_400_BAD_REQUEST,
                "One or more subject ids are invalid.",
                details={"invalid_subject_ids": missing},
            )

    # ---------------- user-centric enrollment (admin users page) ----------------

    async def list_enrolled_for_user(self, user_id: str) -> List[SubjectResponse]:
        user = await self._users.get(user_id)
        if user is None:
            raise APIError(
                ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "User not found."
            )
        if user.role != UserRole.STUDENT:
            return []
        ids = await self._subjects.subject_ids_for_student(user_id)
        if not ids:
            return []
        out: List[SubjectResponse] = []
        for sid in ids:
            s = await self._subjects.get(sid)
            if s is not None:
                out.append(await self._to_response(s))
        return out

    async def set_enrolled_for_user(
        self, actor: User, user_id: str, subject_ids: List[str]
    ) -> List[SubjectResponse]:
        user = await self._users.get(user_id)
        if user is None:
            raise APIError(
                ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "User not found."
            )
        if user.role != UserRole.STUDENT:
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                status.HTTP_400_BAD_REQUEST,
                "Enrollment can only be set for student accounts.",
            )
        await self._validate_subject_ids_exist(subject_ids)
        await self._subjects.replace_subjects_for_student(user_id, subject_ids)
        await self._activity.record(
            action="Student enrollment updated",
            actor=actor,
            subject_label=user.name,
            meta={"userId": user_id, "subjectIds": list(subject_ids)},
        )
        return await self.list_enrolled_for_user(user_id)


def _format_pdf_count(n: int) -> str:
    if n == 0:
        return "0 PDFs"
    if n == 1:
        return "1 PDF"
    return f"{n} PDFs"
