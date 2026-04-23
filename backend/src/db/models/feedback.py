"""Feedback ORM model (spec §8.4)."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin, pg_enum


class FeedbackValue(str, enum.Enum):
    UP = "up"
    DOWN = "down"


def _new_feedback_id() -> str:
    return "fb_" + uuid.uuid4().hex[:16]


class Feedback(Base, TimestampMixin):
    __tablename__ = "feedbacks"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=_new_feedback_id)
    message_id: Mapped[str] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    feedback: Mapped[FeedbackValue] = mapped_column(
        pg_enum(FeedbackValue, name="feedback_value"), nullable=False
    )
