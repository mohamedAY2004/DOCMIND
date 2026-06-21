"""Subject, instructor-roster, and semester endpoints (spec §6)."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, UserRole
from helpers.errors import APIError, ErrorCode
from helpers.deps import (
    get_current_user,
    get_session,
    require_role,
    require_student_access,
    require_subject_access,
)
from helpers.pagination import Page, PaginationParams, admin_pagination_query
from schemas.semester import (
    CreateSemesterRequest,
    SemesterResponse,
    UpdateSemesterRequest,
)
from schemas.subject import (
    CreateSubjectRequest,
    InstructorResponse,
    StudentResponse,
    SubjectResponse,
    UpdateSubjectRequest,
)
from services.semester_service import SemesterService
from services.subject_service import SubjectService

subjects_router = APIRouter(prefix="/subjects", tags=["subjects"])
admin_subjects_router = APIRouter(prefix="/admin/subjects", tags=["admin", "subjects"])
semesters_router = APIRouter(prefix="/semesters", tags=["subjects"])
admin_semesters_router = APIRouter(
    prefix="/admin/semesters", tags=["admin", "subjects"]
)


@subjects_router.get("/student", response_model=List[SubjectResponse])
async def list_subjects_for_student(
    session: AsyncSession = Depends(get_session),
    student: User = Depends(require_role(UserRole.STUDENT)),
    _: User = Depends(require_student_access),
) -> List[SubjectResponse]:
    return await SubjectService(session).list_for_student(student)


@subjects_router.get("/instructor", response_model=List[SubjectResponse])
async def list_subjects_for_instructor(
    instructorId: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN)),
) -> List[SubjectResponse]:
    return await SubjectService(session).list_for_instructor(user, instructorId)


# Sub-routes MUST be registered before ``/{subject_id}`` so the single-segment
# pattern does not take precedence over ``/{subject_id}/instructors`` on some
# Starlette/FastAPI versions and proxies.
@subjects_router.get(
    "/{subject_id}/instructors", response_model=List[InstructorResponse]
)
async def list_subject_instructors(
    subject_id: str,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(require_subject_access),
) -> List[InstructorResponse]:
    return await SubjectService(session).list_instructors(subject_id)


@subjects_router.get(
    "/{subject_id}/students", response_model=List[StudentResponse]
)
async def list_subject_students(
    subject_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.INSTRUCTOR)),
) -> List[StudentResponse]:
    service = SubjectService(session)
    if user.role == UserRole.INSTRUCTOR and not await service.is_instructor_of(
        subject_id, user.id
    ):
        raise APIError(
            ErrorCode.FORBIDDEN,
            status.HTTP_403_FORBIDDEN,
            "You are not assigned to this subject.",
        )
    return await service.list_students(subject_id)


@subjects_router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    subject_id: str,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(require_subject_access),
) -> SubjectResponse:
    return await SubjectService(session).get(subject_id)


@semesters_router.get("", response_model=List[SemesterResponse])
async def list_semesters(
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_current_user),
) -> List[SemesterResponse]:
    return await SemesterService(session).list_all()


@semesters_router.get("/current", response_model=List[SemesterResponse])
async def list_current_semesters(
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_current_user),
) -> List[SemesterResponse]:
    return await SemesterService(session).get_current()


# ------------------ admin writes (spec §6.7) ------------------


@admin_subjects_router.get("", response_model=Page[SubjectResponse])
async def list_admin_subjects(
    semesterId: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
    params: PaginationParams = Depends(admin_pagination_query),
) -> Page[SubjectResponse]:
    items, total = await SubjectService(session).list_paginated(
        search=params.search,
        semester_id=semesterId,
        offset=params.offset,
        limit=params.page_size,
    )
    return Page.build(items=items, total=total, params=params)


@admin_subjects_router.post("", response_model=SubjectResponse, status_code=201)
async def create_subject(
    body: CreateSubjectRequest,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_role(UserRole.ADMIN)),
) -> SubjectResponse:
    return await SubjectService(session).create(admin, body)


@admin_subjects_router.patch("/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: str,
    body: UpdateSubjectRequest,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_role(UserRole.ADMIN)),
) -> SubjectResponse:
    return await SubjectService(session).update(admin, subject_id, body)


@admin_subjects_router.delete(
    "/{subject_id}", status_code=204, response_model=None
)
async def delete_subject(
    subject_id: str,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_role(UserRole.ADMIN)),
) -> None:
    await SubjectService(session).delete(admin, subject_id)


# ------------------ admin semester writes (spec §6.6) ------------------


@admin_semesters_router.post("", response_model=SemesterResponse, status_code=201)
async def create_semester(
    body: CreateSemesterRequest,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_role(UserRole.ADMIN)),
) -> SemesterResponse:
    return await SemesterService(session).create(admin, body)


@admin_semesters_router.patch("/{semester_id}", response_model=SemesterResponse)
async def update_semester(
    semester_id: str,
    body: UpdateSemesterRequest,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_role(UserRole.ADMIN)),
) -> SemesterResponse:
    return await SemesterService(session).update(admin, semester_id, body)


@admin_semesters_router.delete(
    "/{semester_id}", status_code=204, response_model=None
)
async def delete_semester(
    semester_id: str,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_role(UserRole.ADMIN)),
) -> None:
    await SemesterService(session).delete(admin, semester_id)
