"""User schemas (spec §9 + §10.1)."""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    id: str
    username: str
    name: str
    # ``str`` (not ``EmailStr``): read-only responses should not re-validate
    # stored data. Pydantic's ``EmailStr`` rejects reserved/special-use dev
    # domains (``.local``, ``.test``, etc.) and would crash any endpoint
    # that serializes such users with a 500.
    email: str
    role: Literal["student", "instructor", "admin"]
    status: Literal["active", "disabled"]
    registeredAt: datetime
    lastActive: Optional[datetime] = None


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    role: Literal["student", "instructor", "admin"]
    password: str = Field(..., min_length=8, max_length=128)
    enrolledSubjectIds: Optional[List[str]] = None


class UpdateUserRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    email: Optional[EmailStr] = None
    role: Optional[Literal["student", "instructor", "admin"]] = None
    enrolledSubjectIds: Optional[List[str]] = None


class ToggleStatusRequest(BaseModel):
    status: Literal["active", "disabled"]


class ResetPasswordResponse(BaseModel):
    temporaryPassword: str


class UserSubjectsRequest(BaseModel):
    subjectIds: List[str] = Field(default_factory=list)
