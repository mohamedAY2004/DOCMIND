"""Grouped statistics with a bounded query count for each subject page."""
from sqlalchemy import func, select
from db.models import (Conversation, ConversationKind, Feedback, FeedbackValue, Material,
                       MaterialStatus, Message, MessageRole, SubjectInstructor, InstructorSubjectRole,
                       User, UserRole)


class SubjectStatsRepository:
    def __init__(self, session):
        self.session = session

    async def for_subjects(self, ids):
        totals = {sid: dict(materials=0, processed=0, interactions=0, responses=0,
                           up=0, down=0, instructors=[], super_id=None) for sid in ids}
        if not ids:
            return totals
        queries = [
            (select(Material.subject_id, func.count(), func.count().filter(Material.status == MaterialStatus.PROCESSED))
             .where(Material.subject_id.in_(ids)).group_by(Material.subject_id), ("materials", "processed")),
            (select(Conversation.subject_id, func.count()).where(Conversation.subject_id.in_(ids),
                 Conversation.kind == ConversationKind.TUTOR).group_by(Conversation.subject_id), ("interactions",)),
            (select(Conversation.subject_id, func.count()).select_from(Message).join(Conversation)
             .where(Conversation.subject_id.in_(ids), Message.role == MessageRole.ASSISTANT)
             .group_by(Conversation.subject_id), ("responses",)),
            (select(Conversation.subject_id, func.count().filter(Feedback.feedback == FeedbackValue.UP),
                    func.count().filter(Feedback.feedback == FeedbackValue.DOWN))
             .select_from(Feedback).join(Message).join(Conversation)
             .where(Conversation.subject_id.in_(ids)).group_by(Conversation.subject_id), ("up", "down")),
        ]
        for query, names in queries:
            for row in (await self.session.execute(query)).all():
                totals[row[0]].update(zip(names, row[1:]))
        roster = await self.session.execute(select(SubjectInstructor.subject_id, SubjectInstructor.user_id,
            SubjectInstructor.instructor_role, User.role).join(User).where(SubjectInstructor.subject_id.in_(ids))
            .order_by(SubjectInstructor.user_id))
        for sid, uid, role, user_role in roster:
            totals[sid]["instructors"].append(uid)
            if role == InstructorSubjectRole.SUPER and user_role == UserRole.INSTRUCTOR:
                totals[sid]["super_id"] = uid
        return totals
