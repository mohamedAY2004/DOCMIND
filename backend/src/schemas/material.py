"""Material schemas (spec §7.1)."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class MaterialResponse(BaseModel):
    id: str
    name: str
    size: str  # pre-formatted per spec
    date: str  # pre-formatted per spec
    status: Literal["indexing", "processed", "failed"]
    uploadedById: str
    uploadedByName: str
    uploadedByInitials: Optional[str] = None
    sizeBytes: Optional[int] = None


class UpdateMaterialRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[Literal["indexing", "processed"]] = None
