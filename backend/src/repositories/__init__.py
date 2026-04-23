"""Repositories own every SQL statement in the project.

Services talk to repositories; repositories talk to the ORM. Nothing else
touches SQLAlchemy.
"""
from .activity_repository import ActivityRepository
from .base import BaseRepository
from .conversation_repository import ConversationRepository
from .document_file_repository import DocumentFileRepository
from .feedback_repository import FeedbackRepository
from .material_repository import MaterialRepository
from .message_repository import MessageRepository
from .semester_repository import SemesterRepository
from .subject_repository import SubjectRepository
from .system_flag_repository import SystemFlagRepository
from .token_blocklist_repository import TokenBlocklistRepository
from .user_repository import UserRepository

__all__ = [
    "ActivityRepository",
    "BaseRepository",
    "ConversationRepository",
    "DocumentFileRepository",
    "FeedbackRepository",
    "MaterialRepository",
    "MessageRepository",
    "SemesterRepository",
    "SubjectRepository",
    "SystemFlagRepository",
    "TokenBlocklistRepository",
    "UserRepository",
]
