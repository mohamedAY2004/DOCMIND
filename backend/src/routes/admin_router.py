"""Admin dashboard routes (spec §10)."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import FeedbackValue, User, UserRole, UserStatus
from helpers.deps import get_session, require_role
from helpers.pagination import Page, PaginationParams, admin_pagination_query
from repositories.feedback_repository import FeedbackRepository
from schemas.admin import (
    ActivityResponse,
    DailyUsageResponse,
    FeedbackRowResponse,
    SubjectStatsResponse,
)
from schemas.subject import SubjectResponse
from schemas.user import (
    CreateUserRequest,
    ResetPasswordResponse,
    ToggleStatusRequest,
    UpdateUserRequest,
    UserResponse,
    UserSubjectsRequest,
)
from services.admin_activity_service import AdminActivityService
from services.admin_stats_service import AdminStatsService
from services.admin_users_service import AdminUsersService
from services.subject_service import SubjectService

users_router = APIRouter(prefix="/admin/users", tags=["admin", "users"])
subjects_stats_router = APIRouter(prefix="/admin/subjects", tags=["admin", "subjects"])
feedback_router = APIRouter(prefix="/admin/feedback", tags=["admin", "feedback"])
activity_router = APIRouter(prefix="/admin/activity", tags=["admin"])
analytics_router = APIRouter(prefix="/admin/analytics", tags=["admin"])


# -------------------- Users --------------------


@users_router.get("", response_model=Page[UserResponse])
async def list_users(
    role: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
    params: PaginationParams = Depends(admin_pagination_query),
) -> Page[UserResponse]:
    role_enum = UserRole(role) if role else None
    return await AdminUsersService(session).list_users(params, role_enum)


@users_router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
) -> UserResponse:
    return await AdminUsersService(session).get(user_id)


@users_router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserRequest,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_role(UserRole.ADMIN)),
) -> UserResponse:
    return await AdminUsersService(session).create(admin, body)


@users_router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    body: UpdateUserRequest,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_role(UserRole.ADMIN)),
) -> UserResponse:
    return await AdminUsersService(session).update(admin, user_id, body)


@users_router.patch("/{user_id}/status", response_model=UserResponse)
async def toggle_user_status(
    user_id: str,
    body: ToggleStatusRequest,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_role(UserRole.ADMIN)),
) -> UserResponse:
    return await AdminUsersService(session).set_status(
        admin, user_id, UserStatus(body.status)
    )


@users_router.post(
    "/{user_id}/reset-password", response_model=ResetPasswordResponse
)
async def reset_user_password(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_role(UserRole.ADMIN)),
) -> ResetPasswordResponse:
    return await AdminUsersService(session).reset_password(admin, user_id)


@users_router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_user(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_role(UserRole.ADMIN)),
) -> None:
    await AdminUsersService(session).delete(admin, user_id)


@users_router.get("/{user_id}/subjects", response_model=List[SubjectResponse])
async def list_user_enrolled_subjects(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
) -> List[SubjectResponse]:
    return await SubjectService(session).list_enrolled_for_user(user_id)


@users_router.put("/{user_id}/subjects", response_model=List[SubjectResponse])
async def set_user_enrolled_subjects(
    user_id: str,
    body: UserSubjectsRequest,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_role(UserRole.ADMIN)),
) -> List[SubjectResponse]:
    return await SubjectService(session).set_enrolled_for_user(
        admin, user_id, body.subjectIds
    )


# -------------------- Subject stats --------------------


@subjects_stats_router.get("/stats", response_model=Page[SubjectStatsResponse])
async def subject_stats(
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
    params: PaginationParams = Depends(admin_pagination_query),
) -> Page[SubjectStatsResponse]:
    return await AdminStatsService(session).list_subject_stats(params)


# -------------------- Feedback report --------------------


@feedback_router.get("", response_model=Page[FeedbackRowResponse])
async def feedback_rows(
    semester: Optional[str] = Query(None),
    subjectId: Optional[str] = Query(None),
    feedback: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
    params: PaginationParams = Depends(admin_pagination_query),
) -> Page[FeedbackRowResponse]:
    fb_enum = FeedbackValue(feedback) if feedback else None
    rows, total = await FeedbackRepository(session).list_rows(
        semester=semester,
        subject_id=subjectId,
        feedback=fb_enum,
        search=params.search,
        offset=params.offset,
        limit=params.page_size,
    )
    items = [FeedbackRowResponse(**r) for r in rows]
    return Page.build(items=items, total=total, params=params)


# -------------------- Activity --------------------


@activity_router.get("", response_model=List[ActivityResponse])
async def activity_feed(
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
) -> List[ActivityResponse]:
    return await AdminActivityService(session).list_recent(limit=limit)


# -------------------- Analytics --------------------


@analytics_router.get("/daily", response_model=List[DailyUsageResponse])
async def analytics_daily(
    days: int = Query(14, ge=1, le=90),
    semesterId: Optional[str] = Query(None),
    subjectId: Optional[str] = Query(None),
    instructorId: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
) -> List[DailyUsageResponse]:
    return await AdminStatsService(session).daily_usage(
        days=days,
        semester_id=semesterId,
        subject_id=subjectId,
        instructor_id=instructorId,
    )
