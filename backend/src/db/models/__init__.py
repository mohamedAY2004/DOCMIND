"""ORM models for DocMind.

Every SQLAlchemy model lives here, one file per table. Repositories import
from this package; nothing else does.
"""
from .activity import Activity
from .conversation import Conversation, ConversationKind
from .document_file import DocumentFile, DocumentFileStatus
from .feedback import Feedback, FeedbackReason, FeedbackValue
from .evaluation import EvaluationCase, EvaluationResult, EvaluationRun, EvaluationRunStatus, GenerationTelemetry
from .material import Material, MaterialStatus
from .message import GenerationStatus, GroundingStatus, Message, MessageRole
from .refresh_session import RefreshSession
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
    "FeedbackReason",
    "EvaluationCase",
    "EvaluationResult",
    "EvaluationRun",
    "EvaluationRunStatus",
    "GenerationTelemetry",
    "Material",
    "MaterialStatus",
    "Message",
    "MessageRole",
    "GenerationStatus",
    "GroundingStatus",
    "RefreshSession",
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
