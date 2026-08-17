"""Feedback ORM model (spec §8.4)."""
from __future__ import annotations

import enum
import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin, pg_enum


class FeedbackValue(str, enum.Enum):
    UP = "up"
    DOWN = "down"


class FeedbackReason(str, enum.Enum):
    INCORRECT = "incorrect"
    UNSUPPORTED = "unsupported"
    OUTDATED = "outdated"
    UNCLEAR = "unclear"
    INCOMPLETE = "incomplete"
    OTHER = "other"


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
    reason: Mapped[Optional[FeedbackReason]] = mapped_column(
        pg_enum(FeedbackReason, name="feedback_reason"), nullable=True
    )
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    evaluation_case_id: Mapped[Optional[str]] = mapped_column(
        String(40), ForeignKey("evaluation_cases.id", ondelete="SET NULL"), nullable=True
    )
