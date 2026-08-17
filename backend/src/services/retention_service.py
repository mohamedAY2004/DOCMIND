from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select

from db.models import Conversation, Semester, Subject, derive_semester_state


def tutor_expiry(end_date: date | None, created_at: datetime) -> datetime:
    if end_date is None:
        return created_at + timedelta(days=180)
    return datetime.combine(end_date, time.max, tzinfo=timezone.utc) + timedelta(days=30)


def document_expiry(active_semester_end: date | None, created_at: datetime) -> datetime:
    if active_semester_end is None:
        return created_at + timedelta(days=180)
    return datetime.combine(active_semester_end, time.max, tzinfo=timezone.utc) + timedelta(days=30)


async def tutor_expiry_for_subject(session, subject_id: str, created_at: datetime) -> datetime:
    row = (await session.execute(
        select(Semester.end_date)
        .join(Subject, Subject.semester_id == Semester.id)
        .where(Subject.id == subject_id)
    )).first()
    return tutor_expiry(row[0] if row else None, created_at)


async def document_expiry_for_current_term(session, created_at: datetime) -> datetime:
    semesters = (await session.execute(select(Semester))).scalars().all()
    active_ends = [item.end_date for item in semesters if derive_semester_state(item.start_date, item.end_date).value == "active" and item.end_date]
    return document_expiry(max(active_ends) if active_ends else None, created_at)


async def expired_conversations(session, now: datetime | None = None):
    now = now or datetime.now(timezone.utc)
    return (await session.execute(
        select(Conversation).where(Conversation.expires_at.is_not(None), Conversation.expires_at <= now)
    )).scalars().all()
