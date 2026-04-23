"""Semester schemas (spec §6.6)."""
from __future__ import annotations

from pydantic import BaseModel


class SemesterResponse(BaseModel):
    id: str
    label: str
