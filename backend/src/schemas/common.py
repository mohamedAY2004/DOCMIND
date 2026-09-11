"""Shared Pydantic types used across request/response models."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base class for every *Response* schema. Enables ORM compatibility."""

    model_config = ConfigDict(from_attributes=True)
