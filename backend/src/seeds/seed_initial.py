"""Initial seed — populates every DocMind table with realistic demo data.

Run after ``alembic upgrade head``:

    python -m seeds.seed_initial          # from src/
    docker compose run --rm migrate       # via Docker

Tables seeded (≥10 rows each where applicable):
    users (12), semesters (4), subjects (12), subject_instructors (12),
    materials (12), conversations (12), document_files (12), messages (24),
    feedbacks (12), activities (12), student_access_flag (1 singleton)

All inserts are idempotent — re-running is safe.
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

_here = os.path.dirname(os.path.abspath(__file__))
_src = os.path.abspath(os.path.join(_here, os.pardir))
if _src not in sys.path:
    sys.path.insert(0, _src)

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.models.activity import Activity, _new_activity_id
from db.models.conversation import Conversation, ConversationKind, _new_conv_id
from db.models.document_file import DocumentFile, DocumentFileStatus, _new_file_id
from db.models.feedback import Feedback, FeedbackValue, _new_feedback_id
from db.models.material import Material, MaterialStatus, _new_material_id
from db.models.message import Message, MessageRole, _new_message_id
from db.models.semester import Semester
from db.models.subject import Subject
from db.models.subject_instructor import SubjectInstructor
from db.models.subject_student import SubjectStudent
from db.models.system_flag import StudentAccessFlag
from db.models.user import User, UserRole, UserStatus, _new_user_id
from helpers.auth import hash_password
from helpers.config import get_settings

_NOW = datetime.now(timezone.utc)


def _ago(days: int = 0, hours: int = 0) -> datetime:
    return _NOW - timedelta(days=days, hours=hours)


# ---------------------------------------------------------------------------
# Raw seed specs
# ---------------------------------------------------------------------------

_USERS = [
    # admins
    {"username": "admin",      "name": "System Admin",        "email": "admin@docmind.local",       "role": UserRole.ADMIN,       "password": "admin123"},
    {"username": "superadmin", "name": "Super Admin",         "email": "superadmin@docmind.local",  "role": UserRole.ADMIN,       "password": "admin123"},
    # instructors
    {"username": "instructor",  "name": "Dr. Alice Martin",   "email": "alice@docmind.local",       "role": UserRole.INSTRUCTOR,  "password": "instructor123"},
    {"username": "bob_prof",    "name": "Prof. Bob Chen",     "email": "bob@docmind.local",         "role": UserRole.INSTRUCTOR,  "password": "instructor123"},
    {"username": "carol_inst",  "name": "Dr. Carol Davies",   "email": "carol@docmind.local",       "role": UserRole.INSTRUCTOR,  "password": "instructor123"},
    {"username": "dave_prof",   "name": "Prof. Dave Singh",   "email": "dave@docmind.local",        "role": UserRole.INSTRUCTOR,  "password": "instructor123"},
    # students
    {"username": "student",     "name": "Demo Student",       "email": "student@docmind.local",     "role": UserRole.STUDENT,     "password": "student123"},
    {"username": "emma_s",      "name": "Emma Wilson",        "email": "emma@docmind.local",        "role": UserRole.STUDENT,     "password": "student123"},
    {"username": "liam_s",      "name": "Liam Johnson",       "email": "liam@docmind.local",        "role": UserRole.STUDENT,     "password": "student123"},
    {"username": "sofia_s",     "name": "Sofia Garcia",       "email": "sofia@docmind.local",       "role": UserRole.STUDENT,     "password": "student123"},
    {"username": "noah_s",      "name": "Noah Kim",           "email": "noah@docmind.local",        "role": UserRole.STUDENT,     "password": "student123"},
    {"username": "mia_s",       "name": "Mia Patel",          "email": "mia@docmind.local",         "role": UserRole.STUDENT,     "password": "student123"},
]

_SEMESTERS = [
    {"id": "fall-2023",   "label": "Fall 2023",   "sort_order": 1},
    {"id": "spring-2024", "label": "Spring 2024", "sort_order": 2},
    {"id": "fall-2024",   "label": "Fall 2024",   "sort_order": 3},
    {"id": "spring-2025", "label": "Spring 2025", "sort_order": 4},
]

_SUBJECTS = [
    {"id": "cs101-f24",  "title": "Introduction to Computer Science", "description": "Fundamentals of programming, algorithms, and computational thinking.", "course_code": "CS101", "semester_id": "fall-2024",   "instructors": ["instructor", "bob_prof"], "students": ["student", "emma_s", "liam_s", "sofia_s"]},
    {"id": "cs201-f24",  "title": "Data Structures & Algorithms",     "description": "Arrays, linked lists, trees, graphs, sorting, and search algorithms.",  "course_code": "CS201", "semester_id": "fall-2024",   "instructors": ["instructor"],              "students": ["student", "liam_s", "noah_s"]},
    {"id": "cs301-f24",  "title": "Database Systems",                 "description": "Relational models, SQL, transactions, normalization, and query optimization.", "course_code": "CS301", "semester_id": "fall-2024",   "instructors": ["carol_inst"],             "students": ["emma_s", "sofia_s", "mia_s"]},
    {"id": "cs401-f24",  "title": "Machine Learning",                 "description": "Supervised and unsupervised learning, neural networks, and model evaluation.", "course_code": "CS401", "semester_id": "fall-2024",   "instructors": ["dave_prof"],              "students": ["liam_s", "noah_s", "mia_s"]},
    {"id": "cs101-sp25", "title": "Introduction to Computer Science", "description": "Fundamentals of programming, algorithms, and computational thinking.", "course_code": "CS101", "semester_id": "spring-2025", "instructors": ["bob_prof"],               "students": ["emma_s", "noah_s"]},
    {"id": "cs202-sp25", "title": "Operating Systems",               "description": "Processes, threads, memory management, file systems, and I/O.",         "course_code": "CS202", "semester_id": "spring-2025", "instructors": ["carol_inst","instructor"],             "students": ["sofia_s", "liam_s", "noah_s"]},
    {"id": "cs305-sp25", "title": "Computer Networks",               "description": "OSI model, TCP/IP, routing, network security, and distributed systems.",  "course_code": "CS305", "semester_id": "spring-2025", "instructors": ["dave_prof"],              "students": ["noah_s", "mia_s", "emma_s"]},
    {"id": "cs402-sp25", "title": "Natural Language Processing",     "description": "Text processing, language models, transformers, and NLP applications.",   "course_code": "CS402", "semester_id": "spring-2025", "instructors": ["instructor", "dave_prof"],"students": ["mia_s", "liam_s", "student"]},
    {"id": "math201-f24","title": "Linear Algebra",                  "description": "Vectors, matrices, eigenvalues, and applications in data science.",       "course_code": "MATH201","semester_id": "fall-2024",  "instructors": ["bob_prof"],               "students": ["sofia_s", "noah_s", "student"]},
    {"id": "math301-sp25","title": "Probability & Statistics",       "description": "Probability theory, distributions, hypothesis testing, and regression.",   "course_code": "MATH301","semester_id": "spring-2025","instructors": ["carol_inst"],             "students": ["mia_s", "emma_s"]},
    {"id": "cs310-f23",  "title": "Software Engineering",            "description": "SDLC, design patterns, testing, CI/CD, and agile methodologies.",         "course_code": "CS310", "semester_id": "fall-2023",   "instructors": ["instructor"],              "students": ["sofia_s"]},
    {"id": "cs410-sp24", "title": "Computer Vision",                 "description": "Image processing, convolutional networks, object detection, and segmentation.", "course_code": "CS410", "semester_id": "spring-2024", "instructors": ["dave_prof","instructor"], "students": ["liam_s", "mia_s"]},
]

_MATERIAL_SPECS = [
    ("cs101-f24",   "Lecture 1 - Intro to Programming.pdf",      1_200_000, "application/pdf",                  "materials/cs101-f24/lecture1.pdf",       MaterialStatus.PROCESSED, "instructor"),
    ("cs101-f24",   "Lecture 2 - Control Flow.pdf",              980_000,   "application/pdf",                  "materials/cs101-f24/lecture2.pdf",       MaterialStatus.PROCESSED, "instructor"),
    ("cs201-f24",   "Week 1 - Arrays and Lists.pdf",             1_500_000, "application/pdf",                  "materials/cs201-f24/week1.pdf",          MaterialStatus.PROCESSED, "instructor"),
    ("cs201-f24",   "Week 2 - Trees.pptx",                       2_100_000, "application/vnd.ms-powerpoint",    "materials/cs201-f24/week2.pptx",         MaterialStatus.PROCESSED, "instructor"),
    ("cs301-f24",   "Relational Model.pdf",                      870_000,   "application/pdf",                  "materials/cs301-f24/relational.pdf",     MaterialStatus.PROCESSED, "carol_inst"),
    ("cs401-f24",   "Introduction to ML.pptx",                   3_400_000, "application/vnd.ms-powerpoint",    "materials/cs401-f24/intro_ml.pptx",      MaterialStatus.PROCESSED, "dave_prof"),
    ("cs202-sp25",  "Process Management.pdf",                    1_100_000, "application/pdf",                  "materials/cs202-sp25/processes.pdf",     MaterialStatus.PROCESSED, "carol_inst"),
    ("cs305-sp25",  "TCP-IP Deep Dive.pdf",                      2_300_000, "application/pdf",                  "materials/cs305-sp25/tcpip.pdf",         MaterialStatus.PROCESSED, "dave_prof"),
    ("cs402-sp25",  "Transformers Explained.pptx",               4_500_000, "application/vnd.ms-powerpoint",    "materials/cs402-sp25/transformers.pptx", MaterialStatus.INDEXING,  "instructor"),
    ("math201-f24", "Vectors and Spaces.pdf",                    760_000,   "application/pdf",                  "materials/math201-f24/vectors.pdf",      MaterialStatus.PROCESSED, "bob_prof"),
    ("math301-sp25","Probability Distributions.pdf",             920_000,   "application/pdf",                  "materials/math301-sp25/distributions.pdf",MaterialStatus.PROCESSED,"carol_inst"),
    ("cs310-f23",   "Agile and Scrum.pptx",                      1_800_000, "application/vnd.ms-powerpoint",    "materials/cs310-f23/agile.pptx",         MaterialStatus.PROCESSED, "instructor"),
]

# (owner_username, kind, subject_id, title)
_CONV_SPECS = [
    ("student",  ConversationKind.TUTOR, "cs101-f24",  "Help with loops"),
    ("student",  ConversationKind.TUTOR, "cs201-f24",  "Binary tree traversal"),
    ("emma_s",   ConversationKind.TUTOR, "cs301-f24",  "SQL joins question"),
    ("emma_s",   ConversationKind.DOC,   None,         "Lecture notes summary"),
    ("liam_s",   ConversationKind.TUTOR, "cs401-f24",  "Gradient descent help"),
    ("liam_s",   ConversationKind.DOC,   None,         "ML paper review"),
    ("sofia_s",  ConversationKind.TUTOR, "math201-f24","Eigenvalues practice"),
    ("sofia_s",  ConversationKind.TUTOR, "cs202-sp25", "Scheduling algorithms"),
    ("noah_s",   ConversationKind.TUTOR, "cs305-sp25", "TCP handshake"),
    ("noah_s",   ConversationKind.DOC,   None,         "Networks notes"),
    ("mia_s",    ConversationKind.TUTOR, "cs402-sp25", "Attention mechanism"),
    ("mia_s",    ConversationKind.TUTOR, "math301-sp25","Bayesian inference"),
]

# (user_q, assistant_reply)
_MESSAGE_PAIRS = [
    ("Can you explain for loops?",                         "Sure! A for loop iterates over a sequence. For example: `for i in range(10): print(i)` prints 0 through 9."),
    ("What is the difference between a stack and queue?",  "A stack is LIFO (Last In First Out), while a queue is FIFO (First In First Out). Stacks use push/pop; queues use enqueue/dequeue."),
    ("How do I write a LEFT JOIN?",                        "A LEFT JOIN returns all rows from the left table and matched rows from the right. Example: `SELECT * FROM a LEFT JOIN b ON a.id = b.a_id`."),
    ("Summarise the document for me.",                     "The document covers three main topics: introduction to neural networks, backpropagation, and regularisation techniques. Let me know which part to expand on."),
    ("How does gradient descent work?",                    "Gradient descent minimises a loss function by iteratively moving in the direction of the negative gradient. The learning rate controls the step size."),
    ("What does this paper say about attention?",          "The paper introduces self-attention, which lets each token attend to all other tokens, replacing recurrence with parallelisable matrix operations."),
    ("Prove that A is an eigenvalue.",                     "An eigenvalue λ satisfies det(A - λI) = 0. Solving this characteristic polynomial gives you the eigenvalues of matrix A."),
    ("What is a process vs a thread?",                     "A process has its own memory space; threads share memory within a process. Threads are lighter and faster to create, but require synchronisation."),
    ("Explain the TCP three-way handshake.",               "Step 1: Client sends SYN. Step 2: Server replies SYN-ACK. Step 3: Client sends ACK. After this the connection is established."),
    ("Summarise these lecture slides.",                    "The slides cover: (1) OSI model layers, (2) IP addressing and subnetting, and (3) routing protocols including OSPF and BGP."),
    ("What is a transformer model?",                      "A transformer uses self-attention and feed-forward layers arranged in an encoder-decoder structure. It processes sequences in parallel, unlike RNNs."),
    ("What is Bayes' theorem?",                           "Bayes' theorem: P(A|B) = P(B|A)·P(A) / P(B). It updates the probability of A given new evidence B."),
]

_ACTIVITY_SPECS = [
    ("admin",      "Created user 'instructor'",               "Dr. Alice Martin",  {"role": "instructor"}),
    ("admin",      "Created user 'bob_prof'",                 "Prof. Bob Chen",    {"role": "instructor"}),
    ("admin",      "Created subject 'cs101-f24'",             "CS101 Fall 2024",   {"course_code": "CS101"}),
    ("admin",      "Created subject 'cs201-f24'",             "CS201 Fall 2024",   {"course_code": "CS201"}),
    ("admin",      "Enabled student access",                  None,                {"enabled": True}),
    ("instructor", "Uploaded material 'Lecture 1'",           "CS101 Fall 2024",   {"size_bytes": 1200000}),
    ("instructor", "Uploaded material 'Lecture 2'",           "CS101 Fall 2024",   {"size_bytes": 980000}),
    ("carol_inst", "Uploaded material 'Relational Model'",    "CS301 Fall 2024",   {"size_bytes": 870000}),
    ("dave_prof",  "Uploaded material 'Intro to ML'",         "CS401 Fall 2024",   {"size_bytes": 3400000}),
    ("admin",      "Disabled student access for maintenance", None,                {"enabled": False}),
    ("admin",      "Re-enabled student access",               None,                {"enabled": True}),
    ("superadmin", "Promoted user 'instructor' to admin",     "Dr. Alice Martin",  {"old_role": "instructor", "new_role": "admin"}),
]


# ---------------------------------------------------------------------------
# Seeder helpers
# ---------------------------------------------------------------------------

def _log(action: str, label: str) -> None:
    print(f"  [{action:6}] {label}")


async def _seed_users(session: AsyncSession) -> dict[str, str]:
    """Returns username → id mapping for use in later seeders."""
    id_map: dict[str, str] = {}
    for spec in _USERS:
        row = await session.scalar(select(User).where(User.username == spec["username"]))
        if row:
            _log("skip", f"user '{spec['username']}'")
            id_map[spec["username"]] = row.id
            continue
        uid = _new_user_id()
        session.add(User(
            id=uid,
            username=spec["username"],
            name=spec["name"],
            email=spec["email"],
            role=spec["role"],
            status=UserStatus.ACTIVE,
            password_hash=hash_password(spec["password"]),
            registered_at=_ago(days=60),
        ))
        id_map[spec["username"]] = uid
        _log("insert", f"user '{spec['username']}' ({spec['role'].value})")
    await session.flush()
    return id_map


async def _seed_semesters(session: AsyncSession) -> None:
    for spec in _SEMESTERS:
        if await session.get(Semester, spec["id"]):
            _log("skip", f"semester '{spec['id']}'")
            continue
        session.add(Semester(**spec))
        _log("insert", f"semester '{spec['label']}'")
    await session.flush()


async def _seed_subjects(session: AsyncSession, uid_map: dict[str, str]) -> None:
    for spec in _SUBJECTS:
        sid = spec["id"]
        if await session.get(Subject, sid):
            _log("skip", f"subject '{sid}'")
        else:
            session.add(Subject(
                id=sid,
                title=spec["title"],
                description=spec["description"],
                course_code=spec["course_code"],
                semester_id=spec["semester_id"],
            ))
            _log("insert", f"subject '{sid}'")

        # subject_instructors (composite PK — safe to re-insert)
        for uname in spec["instructors"]:
            uid = uid_map.get(uname)
            if not uid:
                continue
            existing = await session.get(SubjectInstructor, {"subject_id": sid, "user_id": uid})
            if existing:
                continue
            session.add(SubjectInstructor(subject_id=sid, user_id=uid))
            _log("insert", f"  subject_instructor {sid} ← {uname}")

        # subject_students (composite PK — safe to re-insert)
        for uname in spec.get("students", []):
            uid = uid_map.get(uname)
            if not uid:
                continue
            existing = await session.get(SubjectStudent, {"subject_id": sid, "user_id": uid})
            if existing:
                continue
            session.add(SubjectStudent(subject_id=sid, user_id=uid))
            _log("insert", f"  subject_student    {sid} ← {uname}")

    await session.flush()


async def _seed_materials(session: AsyncSession, uid_map: dict[str, str]) -> None:
    for (subj_id, name, size, mime, path, status, uploader) in _MATERIAL_SPECS:
        exists = await session.scalar(
            select(Material).where(Material.storage_path == path)
        )
        if exists:
            _log("skip", f"material '{name}'")
            continue
        session.add(Material(
            id=_new_material_id(),
            subject_id=subj_id,
            name=name,
            size_bytes=size,
            mime=mime,
            storage_path=path,
            status=status,
            uploaded_by_id=uid_map.get(uploader),
        ))
        _log("insert", f"material '{name}'")
    await session.flush()


async def _seed_conversations_and_messages(
    session: AsyncSession, uid_map: dict[str, str]
) -> None:
    for i, (owner, kind, subj_id, title) in enumerate(_CONV_SPECS):
        owner_id = uid_map.get(owner)
        if not owner_id:
            continue

        existing_conv = await session.scalar(
            select(Conversation).where(
                Conversation.owner_id == owner_id,
                Conversation.title == title,
            )
        )
        if existing_conv:
            _log("skip", f"conversation '{title}'")
            conv_id = existing_conv.id
        else:
            conv_id = _new_conv_id()
            session.add(Conversation(
                id=conv_id,
                owner_id=owner_id,
                kind=kind,
                subject_id=subj_id,
                title=title,
            ))
            _log("insert", f"conversation '{title}'")
            await session.flush()

            # Seed a document_file for every doc-kind conversation
            if kind == ConversationKind.DOC:
                file_id = _new_file_id()
                session.add(DocumentFile(
                    id=file_id,
                    conversation_id=conv_id,
                    name=f"uploaded_doc_{i + 1}.pdf",
                    size_bytes=500_000 + i * 100_000,
                    mime="application/pdf",
                    storage_path=f"doc_uploads/{conv_id}/file.pdf",
                    status=DocumentFileStatus.READY,
                ))
                _log("insert", f"  document_file for '{title}'")

            # Seed a user+assistant message pair
            pair = _MESSAGE_PAIRS[i % len(_MESSAGE_PAIRS)]
            user_msg_id = _new_message_id()
            asst_msg_id = _new_message_id()
            asst_role = MessageRole.DOC if kind == ConversationKind.DOC else MessageRole.ASSISTANT

            session.add(Message(id=user_msg_id, conversation_id=conv_id, role=MessageRole.USER,  text=pair[0]))
            session.add(Message(id=asst_msg_id, conversation_id=conv_id, role=asst_role,          text=pair[1]))
            _log("insert", f"  messages (×2) for '{title}'")
            await session.flush()

            # Feedback on the assistant message (alternating up/down)
            fb_val = FeedbackValue.UP if i % 3 != 2 else FeedbackValue.DOWN
            session.add(Feedback(
                id=_new_feedback_id(),
                message_id=asst_msg_id,
                user_id=owner_id,
                feedback=fb_val,
            ))
            _log("insert", f"  feedback ({fb_val.value}) for '{title}'")

    await session.flush()


async def _seed_activities(session: AsyncSession, uid_map: dict[str, str]) -> None:
    existing_count = await session.scalar(
        select(Activity).where(Activity.action.ilike("Created user%"))
    )
    if existing_count:
        _log("skip", "activities (already seeded)")
        return
    for i, (actor, action, label, meta) in enumerate(_ACTIVITY_SPECS):
        session.add(Activity(
            id=_new_activity_id(),
            action=action,
            actor_user_id=uid_map.get(actor),
            subject_label=label,
            meta=meta,
        ))
        _log("insert", f"activity '{action[:50]}'")
    await session.flush()


_WIPE_TABLES = [
    "feedbacks",
    "messages",
    "document_files",
    "conversations",
    "activities",
    "materials",
    "subject_students",
    "subject_instructors",
    "subjects",
    "semesters",
    "token_blocklist",
    "student_access_flag",
    "users",
]


async def _wipe_all(session: AsyncSession) -> None:
    """TRUNCATE every DocMind table so the seeder starts from a clean slate."""
    joined = ", ".join(_WIPE_TABLES)
    await session.execute(
        text(f"TRUNCATE TABLE {joined} RESTART IDENTITY CASCADE")
    )
    await session.flush()
    _log("wipe", f"truncated: {joined}")


async def _seed_student_access_flag(session: AsyncSession) -> None:
    if await session.get(StudentAccessFlag, 1):
        _log("skip", "student_access_flag")
        return
    session.add(StudentAccessFlag(id=1, enabled=True, message=""))
    _log("insert", "student_access_flag (enabled=True)")
    await session.flush()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    settings = get_settings()
    url = settings.DATABASE_URL
    for prefix, replacement in [
        ("postgresql://", "postgresql+asyncpg://"),
        ("postgres://",   "postgresql+asyncpg://"),
    ]:
        if url.startswith(prefix):
            url = replacement + url[len(prefix):]
            break

    engine = create_async_engine(url, pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

    async with factory() as session:
        print("\n── Wipe ───────────────────────────────")
        await _wipe_all(session)

        print("\n── Users ──────────────────────────────")
        uid_map = await _seed_users(session)

        print("\n── Semesters ──────────────────────────")
        await _seed_semesters(session)

        print("\n── Subjects & Instructors ─────────────")
        await _seed_subjects(session, uid_map)

        print("\n── Materials ──────────────────────────")
        await _seed_materials(session, uid_map)

        print("\n── Conversations, Files, Messages, Feedbacks ──")
        await _seed_conversations_and_messages(session, uid_map)

        print("\n── Activities ─────────────────────────")
        await _seed_activities(session, uid_map)

        print("\n── System Flags ───────────────────────")
        await _seed_student_access_flag(session)

        await session.commit()

    await engine.dispose()
    print("\nSeed complete.\n")


if __name__ == "__main__":
    asyncio.run(main())
