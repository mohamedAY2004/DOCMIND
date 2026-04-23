"""Admin user-management service (spec §10.1)."""
from __future__ import annotations

import secrets
import string
from typing import Optional

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, UserRole, UserStatus
from helpers.auth import hash_password
from helpers.errors import APIError, ErrorCode
from helpers.pagination import Page, PaginationParams
from repositories.activity_repository import ActivityRepository
from repositories.subject_repository import SubjectRepository
from repositories.user_repository import UserRepository
from schemas.user import (
    CreateUserRequest,
    ResetPasswordResponse,
    UpdateUserRequest,
    UserResponse,
)
from services.activity_logger import ActivityLogger


def _to_response(u: User) -> UserResponse:
    return UserResponse(
        id=u.id,
        username=u.username,
        name=u.name,
        email=u.email,
        role=u.role.value,
        status=u.status.value,
        registeredAt=u.registered_at,
        lastActive=u.last_active,
    )


class AdminUsersService:
    def __init__(self, session: AsyncSession) -> None:
        self._users = UserRepository(session)
        self._subjects = SubjectRepository(session)
        self._activity = ActivityLogger(ActivityRepository(session))

    async def _apply_enrollment(
        self, user: User, subject_ids: Optional[list[str]]
    ) -> None:
        """Validate + replace subject enrollment for student users.

        No-op for non-students (raises if caller tried to set it anyway).
        """
        if subject_ids is None:
            return
        if user.role != UserRole.STUDENT:
            if subject_ids:
                raise APIError(
                    ErrorCode.VALIDATION_ERROR,
                    status.HTTP_400_BAD_REQUEST,
                    "Only student accounts can be enrolled in subjects.",
                )
            return
        # Validate all subject ids exist.
        missing: list[str] = []
        for sid in subject_ids:
            if await self._subjects.get(sid) is None:
                missing.append(sid)
        if missing:
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                status.HTTP_400_BAD_REQUEST,
                "One or more subject ids are invalid.",
                details={"invalid_subject_ids": missing},
            )
        await self._subjects.replace_subjects_for_student(user.id, subject_ids)

    async def list_users(
        self,
        params: PaginationParams,
        role: Optional[UserRole],
    ) -> Page[UserResponse]:
        rows, total = await self._users.search(
            search=params.search,
            role=role,
            offset=params.offset,
            limit=params.page_size,
        )
        return Page.build(
            items=[_to_response(r) for r in rows], total=total, params=params
        )

    async def get(self, user_id: str) -> UserResponse:
        u = await self._users.get(user_id)
        if u is None:
            raise APIError(
                ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "User not found."
            )
        return _to_response(u)

    async def create(self, actor: User, body: CreateUserRequest) -> UserResponse:
        if await self._users.get_by_username(body.username) is not None:
            raise APIError(
                ErrorCode.CONFLICT,
                status.HTTP_409_CONFLICT,
                "Username already taken.",
            )
        if await self._users.get_by_email(body.email) is not None:
            raise APIError(
                ErrorCode.CONFLICT,
                status.HTTP_409_CONFLICT,
                "Email already in use.",
            )
        user = User(
            username=body.username,
            name=body.name,
            email=body.email,
            role=UserRole(body.role),
            password_hash=hash_password(body.password),
        )
        await self._users.add(user)
        await self._apply_enrollment(user, body.enrolledSubjectIds)
        await self._activity.record(
            action=f"{user.role.value.title()} account created",
            actor=actor,
            subject_label=user.name,
            meta={"userId": user.id},
        )
        return _to_response(user)

    async def update(
        self, actor: User, user_id: str, body: UpdateUserRequest
    ) -> UserResponse:
        user = await self._users.get(user_id)
        if user is None:
            raise APIError(
                ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "User not found."
            )
        if body.email is not None and body.email.lower() != user.email.lower():
            other = await self._users.get_by_email(body.email)
            if other is not None and other.id != user.id:
                raise APIError(
                    ErrorCode.CONFLICT,
                    status.HTTP_409_CONFLICT,
                    "Email already in use.",
                )
            user.email = body.email
        if body.name is not None:
            user.name = body.name
        if body.role is not None:
            user.role = UserRole(body.role)
        await self._apply_enrollment(user, body.enrolledSubjectIds)
        await self._activity.record(
            action="User updated",
            actor=actor,
            subject_label=user.name,
            meta={"userId": user.id},
        )
        return _to_response(user)

    async def set_status(
        self, actor: User, user_id: str, new_status: UserStatus
    ) -> UserResponse:
        if actor.id == user_id and new_status == UserStatus.DISABLED:
            raise APIError(
                ErrorCode.CANNOT_DISABLE_SELF,
                status.HTTP_409_CONFLICT,
                "Admins cannot disable their own account.",
            )
        user = await self._users.get(user_id)
        if user is None:
            raise APIError(
                ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "User not found."
            )
        await self._users.set_status(user_id, new_status)
        user.status = new_status
        await self._activity.record(
            action=(
                "User disabled"
                if new_status == UserStatus.DISABLED
                else "User enabled"
            ),
            actor=actor,
            subject_label=user.name,
            meta={"userId": user.id},
        )
        return _to_response(user)

    async def delete(self, actor: User, user_id: str) -> None:
        if actor.id == user_id:
            raise APIError(
                ErrorCode.CANNOT_DISABLE_SELF,
                status.HTTP_409_CONFLICT,
                "Admins cannot delete their own account.",
            )
        user = await self._users.get(user_id)
        if user is None:
            raise APIError(
                ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "User not found."
            )
        await self._activity.record(
            action="User deleted",
            actor=actor,
            subject_label=user.name,
            meta={"userId": user.id},
        )
        await self._users.delete(user)

    async def reset_password(
        self, actor: User, user_id: str
    ) -> ResetPasswordResponse:
        user = await self._users.get(user_id)
        if user is None:
            raise APIError(
                ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "User not found."
            )
        temp = _generate_temp_password()
        user.password_hash = hash_password(temp)
        await self._activity.record(
            action="Password reset",
            actor=actor,
            subject_label=user.name,
            meta={"userId": user.id},
        )
        return ResetPasswordResponse(temporaryPassword=temp)


def _generate_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))
