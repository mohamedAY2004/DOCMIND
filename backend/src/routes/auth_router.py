"""Auth routes (spec §4)."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User
from helpers.config import get_settings
from helpers.deps import get_current_user, get_logout_claims, get_session
from helpers.errors import APIError, ErrorCode
from repositories.user_repository import UserRepository
from schemas.auth import (
    BrowserSessionResponse,
    LoginRequest,
    LoginResponse,
    MeResponse,
    PortalTicketRequest,
    PortalTicketResponse,
    SSOExchangeRequest,
    SSOStartResponse,
    UserSummary,
)
from services.auth_service import AuthService
from services.browser_session_service import BrowserSessionService, clear_browser_cookies, set_browser_cookies
from services.ephemeral_store import store_for
from services.portal_sso_service import PortalSSOService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> LoginResponse:
    if not get_settings().LOCAL_AUTH_ENABLED:
        raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Local login is disabled.")
    result = await AuthService(session).login(body.username, body.password)
    user = await UserRepository(session).get(result.user.id)
    browser = await BrowserSessionService(session).issue(user)
    set_browser_cookies(response, browser)
    return result


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def logout(
    request: Request,
    response: Response,
    claims: tuple[str, datetime] = Depends(get_logout_claims),
    session: AsyncSession = Depends(get_session),
) -> Response:
    jti, expires_at = claims
    await AuthService(session).logout(jti, expires_at)
    await BrowserSessionService(session).revoke(
        request.cookies.get("docmind_refresh")
    )
    clear_browser_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/refresh", response_model=BrowserSessionResponse)
async def refresh(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> BrowserSessionResponse:
    raw = request.cookies.get("docmind_refresh")
    if not raw:
        raise APIError(ErrorCode.UNAUTHENTICATED, status.HTTP_401_UNAUTHORIZED, "Missing refresh session.")
    user, browser = await BrowserSessionService(session).rotate(raw)
    set_browser_cookies(response, browser)
    return _browser_response(user)


@router.post("/sso/start", response_model=SSOStartResponse)
async def sso_start(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> SSOStartResponse:
    if not get_settings().PORTAL_SSO:
        raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Portal SSO is disabled.")
    state, portal_url = await PortalSSOService(session, store_for(request.app)).start()
    return SSOStartResponse(state=state, portalUrl=portal_url, expiresIn=300)


@router.post("/sso/ticket", response_model=PortalTicketResponse)
async def create_portal_ticket(
    body: PortalTicketRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> PortalTicketResponse:
    if not get_settings().PORTAL_SSO:
        raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Portal SSO is disabled.")
    code = await PortalSSOService(session, store_for(request.app)).create_ticket(
        state=body.state,
        user_id=body.userId,
        issued_at=body.issuedAt,
        signature=body.signature,
    )
    return PortalTicketResponse(code=code, expiresIn=60)


@router.post("/sso/exchange", response_model=BrowserSessionResponse)
async def sso_exchange(
    body: SSOExchangeRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> BrowserSessionResponse:
    if not get_settings().PORTAL_SSO:
        raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Portal SSO is disabled.")
    user = await PortalSSOService(session, store_for(request.app)).exchange(
        state=body.state, code=body.code
    )
    browser = await BrowserSessionService(session).issue(user)
    set_browser_cookies(response, browser)
    return _browser_response(user)


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


def _browser_response(user: User) -> BrowserSessionResponse:
    redirects = {"student": "/home", "instructor": "/instructor", "admin": "/admin"}
    return BrowserSessionResponse(
        user=UserSummary(
            id=user.id,
            username=user.username,
            name=user.name,
            role=user.role.value,
        ),
        redirect=redirects[user.role.value],
    )
