"""System-access schemas (spec §5)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StudentAccessResponse(BaseModel):
    enabled: bool
    message: str = ""
    updatedAt: Optional[datetime] = None


class UpdateStudentAccessRequest(BaseModel):
    enabled: bool
    # Explicit empty string clears the stored message (spec §5.2).
    message: Optional[str] = Field(None, max_length=500)
