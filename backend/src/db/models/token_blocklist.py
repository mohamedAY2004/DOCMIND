"""Revoked-JWT blocklist (spec §4.2 — logout MUST revoke the token)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin


class TokenBlocklist(Base, TimestampMixin):
    __tablename__ = "token_blocklist"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
