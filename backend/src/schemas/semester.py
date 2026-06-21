"""Semester schemas (spec §6.6)."""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class SemesterResponse(BaseModel):
    id: str
    label: str
    sortOrder: int = 0
    startDate: Optional[date] = None
    endDate: Optional[date] = None
    state: str  # 'upcoming' | 'active' | 'archived' (derived from the dates)
    isCurrent: bool = False  # convenience flag == (state == 'active')


class CreateSemesterRequest(BaseModel):
    id: str = Field(..., min_length=2, max_length=64)
    label: str = Field(..., min_length=1, max_length=120)
    sortOrder: int = 0
    startDate: Optional[date] = None
    endDate: Optional[date] = None


class UpdateSemesterRequest(BaseModel):
    label: Optional[str] = Field(None, min_length=1, max_length=120)
    sortOrder: Optional[int] = None
    startDate: Optional[date] = None
    endDate: Optional[date] = None
