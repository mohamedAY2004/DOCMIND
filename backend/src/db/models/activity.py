"""Activity ORM model (spec §10.5). Every admin-visible mutation logs here."""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin


def _new_activity_id() -> str:
    return "A-" + uuid.uuid4().hex[:12].upper()


class Activity(Base, TimestampMixin):
    __tablename__ = "activities"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_activity_id)
    action: Mapped[str] = mapped_column(String(160), nullable=False)
    actor_user_id: Mapped[Optional[str]] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Free-form display label for the "user" column on the admin dashboard.
    # Falls back to the actor's name when they still exist.
    subject_label: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
