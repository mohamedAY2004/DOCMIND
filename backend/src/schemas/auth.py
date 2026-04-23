"""Auth request / response schemas (spec §4)."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .common import ORMModel


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class UserSummary(ORMModel):
    id: str
    username: str
    name: str
    role: str


class LoginResponse(BaseModel):
    token: str
    user: UserSummary
    redirect: str
    welcomeMessage: Optional[str] = None


class MeResponse(BaseModel):
    user: UserSummary
