"""ORM models for DocMind.

Every SQLAlchemy model lives here, one file per table. Repositories import
from this package; nothing else does.
"""
from .activity import Activity
from .conversation import Conversation, ConversationKind
from .document_file import DocumentFile, DocumentFileStatus
from .feedback import Feedback, FeedbackValue
from .material import Material, MaterialStatus
from .message import Message, MessageRole
from .semester import Semester, SemesterState, derive_semester_state
from .subject import Subject
from .subject_instructor import InstructorSubjectRole, SubjectInstructor
from .subject_student import SubjectStudent
from .system_flag import StudentAccessFlag
from .token_blocklist import TokenBlocklist
from .user import User, UserRole, UserStatus

__all__ = [
    "Activity",
    "Conversation",
    "ConversationKind",
    "DocumentFile",
    "DocumentFileStatus",
    "Feedback",
    "FeedbackValue",
    "Material",
    "MaterialStatus",
    "Message",
    "MessageRole",
    "Semester",
    "SemesterState",
    "derive_semester_state",
    "Subject",
    "InstructorSubjectRole",
    "SubjectInstructor",
    "SubjectStudent",
    "StudentAccessFlag",
    "TokenBlocklist",
    "User",
    "UserRole",
    "UserStatus",
]
