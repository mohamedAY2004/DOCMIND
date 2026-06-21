"""Subject schemas (spec §6.1)."""
from __future__ import annotations

import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

SLUG_RE = re.compile(r"^[a-z0-9-]{2,64}$")


class SubjectResponse(BaseModel):
    id: str
    title: str
    description: str
    courseCode: str
    semesterId: Optional[str] = None
    pdfCount: str  # pre-formatted; spec §6.1 mandates string type
    instructorIds: List[str]
    superInstructorId: Optional[str] = None
    studentIds: List[str] = Field(default_factory=list)
    studentCount: int = 0
    # Derived lifecycle state of the subject's semester (Tier 2A). Drives the
    # student UI's read-only treatment of past terms. 'active' when the subject
    # has no semester (fail-open), matching the backend gate.
    semesterState: str = "active"  # 'upcoming' | 'active' | 'archived'


class InstructorResponse(BaseModel):
    id: str
    username: str
    name: str
    # ``str`` (not ``EmailStr``) — emails are already validated on admin
    # input; re-validating on the way out fails for reserved/special-use
    # dev domains such as ``@docmind.local`` and would turn a read-only
    # roster fetch into a 500.
    email: str
    instructorRole: str  # 'super' | 'viewer'


class StudentResponse(BaseModel):
    id: str
    name: str
    email: str


class CreateSubjectRequest(BaseModel):
    id: str = Field(..., min_length=2, max_length=64)
    title: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1, max_length=500)
    courseCode: str = Field(..., min_length=1, max_length=80)
    semesterId: Optional[str] = Field(None, max_length=64)
    instructorIds: List[str] = Field(default_factory=list)
    superInstructorId: Optional[str] = None
    studentIds: List[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _slug_ok(cls, v: str) -> str:
        if not SLUG_RE.match(v):
            raise ValueError("id must match [a-z0-9-]{2,64}")
        return v


class UpdateSubjectRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    courseCode: Optional[str] = Field(None, min_length=1, max_length=80)
    semesterId: Optional[str] = Field(None, max_length=64)
    instructorIds: Optional[List[str]] = None
    superInstructorId: Optional[str] = None
    studentIds: Optional[List[str]] = None
