"""Unit tests for the date-derived semester lifecycle state.

``derive_semester_state`` is a pure function (no DB) — it is the seam that Tier 2A
access control keys off, so its boundary and null-date behaviour is pinned here.
"""
from __future__ import annotations

from datetime import date

from db.models import SemesterState, derive_semester_state


def test_before_start_is_upcoming() -> None:
    state = derive_semester_state(
        date(2026, 9, 1), date(2026, 12, 31), today=date(2026, 8, 31)
    )
    assert state is SemesterState.UPCOMING


def test_within_window_is_active() -> None:
    state = derive_semester_state(
        date(2026, 2, 1), date(2026, 5, 31), today=date(2026, 3, 15)
    )
    assert state is SemesterState.ACTIVE


def test_after_end_is_archived() -> None:
    state = derive_semester_state(
        date(2025, 9, 1), date(2025, 12, 31), today=date(2026, 6, 21)
    )
    assert state is SemesterState.ARCHIVED


def test_boundaries_are_inclusive() -> None:
    start, end = date(2026, 2, 1), date(2026, 5, 31)
    assert derive_semester_state(start, end, today=start) is SemesterState.ACTIVE
    assert derive_semester_state(start, end, today=end) is SemesterState.ACTIVE


def test_null_start_is_never_upcoming() -> None:
    # No start → already begun; still bounded by end.
    assert (
        derive_semester_state(None, date(2026, 5, 31), today=date(2020, 1, 1))
        is SemesterState.ACTIVE
    )
    assert (
        derive_semester_state(None, date(2026, 5, 31), today=date(2027, 1, 1))
        is SemesterState.ARCHIVED
    )


def test_null_end_is_never_archived() -> None:
    # No end → open-ended; still bounded by start.
    assert (
        derive_semester_state(date(2026, 2, 1), None, today=date(2030, 1, 1))
        is SemesterState.ACTIVE
    )
    assert (
        derive_semester_state(date(2026, 2, 1), None, today=date(2025, 1, 1))
        is SemesterState.UPCOMING
    )


def test_both_null_is_active() -> None:
    assert derive_semester_state(None, None) is SemesterState.ACTIVE


def test_default_today_uses_utc_without_raising() -> None:
    # Smoke test: omitting ``today`` must resolve against the current UTC date.
    assert derive_semester_state(None, None) is SemesterState.ACTIVE
