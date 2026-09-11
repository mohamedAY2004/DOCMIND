"""Queries supporting retention policy; expiry decisions live in the service."""
from sqlalchemy import select
from db.models import Conversation, Semester, Subject


class RetentionRepository:
    def __init__(self, session):
        self.session = session

    async def subject_end_date(self, subject_id):
        return (await self.session.execute(select(Semester.end_date)
            .join(Subject, Subject.semester_id == Semester.id).where(Subject.id == subject_id))).scalar()

    async def semesters(self):
        return (await self.session.execute(select(Semester))).scalars().all()

    async def expired(self, now):
        return (await self.session.execute(select(Conversation).where(
            Conversation.expires_at.is_not(None), Conversation.expires_at <= now))).scalars().all()
