"""Semester ORM model (spec §6.6).

Semesters carry an optional ``start_date`` / ``end_date`` window. The lifecycle
state (upcoming / active / archived) is **derived** from that window at read time
via :func:`derive_semester_state` — it is intentionally not stored, so a term
rolls over automatically as the calendar advances (no scheduler, no admin
toggle). This derivation is the single seam per-subject access control keys off.
"""
from __future__ import annotations

import enum
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class SemesterState(str, enum.Enum):
    UPCOMING = "upcoming"   # starts in the future — hidden from students (Tier 2A)
    ACTIVE = "active"       # within the window — fully interactive
    ARCHIVED = "archived"   # ended — read-only (Tier 2A)


def derive_semester_state(
    start: Optional[date],
    end: Optional[date],
    today: Optional[date] = None,
) -> SemesterState:
    """Derive a semester's lifecycle state from its date window.

    Pure function (no DB, no I/O) so it is cheap to call per row and trivially
    testable. ``today`` defaults to the current UTC date.

    Null-date rule (deliberate, fail-open): a missing ``start`` is never
    "upcoming" and a missing ``end`` is never "archived", so a semester with
    unset dates resolves to ``ACTIVE`` rather than silently locking its content.
    The window is inclusive on both ends (``today == start`` / ``today == end``
    are both ``ACTIVE``).
    """
    if today is None:
        today = datetime.now(timezone.utc).date()
    if start is not None and today < start:
        return SemesterState.UPCOMING
    if end is not None and today > end:
        return SemesterState.ARCHIVED
    return SemesterState.ACTIVE


class Semester(Base):
    __tablename__ = "semesters"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
