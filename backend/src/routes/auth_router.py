"""Auth routes (spec §4)."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User
from helpers.deps import get_current_user, get_logout_claims, get_session
from schemas.auth import LoginRequest, LoginResponse, MeResponse
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> LoginResponse:
    return await AuthService(session).login(body.username, body.password)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def logout(
    claims: tuple[str, datetime] = Depends(get_logout_claims),
    session: AsyncSession = Depends(get_session),
) -> Response:
    jti, expires_at = claims
    await AuthService(session).logout(jti, expires_at)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse.model_validate(
        {
            "user": {
                "id": user.id,
                "username": user.username,
                "name": user.name,
                "role": user.role.value,
            }
        }
    )
