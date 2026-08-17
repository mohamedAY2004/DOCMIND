"""Rotating browser refresh-session record."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin


def _new_refresh_id() -> str:
    return "rs_" + uuid.uuid4().hex[:20]


class RefreshSession(Base, TimestampMixin):
    __tablename__ = "refresh_sessions"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_new_refresh_id)
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    replaced_by_id: Mapped[Optional[str]] = mapped_column(
        String(40), ForeignKey("refresh_sessions.id", ondelete="SET NULL")
    )
