"""Student-access endpoints (spec §5)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, UserRole
from helpers.deps import get_session, require_role
from schemas.system_access import StudentAccessResponse, UpdateStudentAccessRequest
from services.system_access_service import SystemAccessService

# Split into two routers so ``GET /system/student-access`` stays public.
public_router = APIRouter(prefix="/system", tags=["system"])
admin_router = APIRouter(prefix="/admin/system", tags=["admin", "system"])


@public_router.get("/student-access", response_model=StudentAccessResponse)
async def get_student_access(
    session: AsyncSession = Depends(get_session),
) -> StudentAccessResponse:
    """Public endpoint — login page uses this to render the banner (spec §5.1)."""
    return await SystemAccessService(session).get()


@admin_router.patch("/student-access", response_model=StudentAccessResponse)
async def update_student_access(
    body: UpdateStudentAccessRequest,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_role(UserRole.ADMIN)),
) -> StudentAccessResponse:
    return await SystemAccessService(session).update(
        actor=admin, enabled=body.enabled, message=body.message
    )
