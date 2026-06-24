"""Initial seed — populates every DocMind table with a large, realistic dataset.

Run after ``alembic upgrade head``:

    python -m seeds.seed_initial          # from src/
    docker compose run --rm migrate       # via Docker

This seed is **procedurally generated** (deterministic via a fixed RNG seed) so it
mimics a busy production environment with enough volume to stress the web / mobile
UI (pagination, search, sorting, analytics, dashboards). Approximate volumes:

    users (~112: 2 admins, 20 instructors, 90 students)
    semesters (7), subjects (~48), subject_instructors (~75), subject_students (~700)
    materials (~400), conversations (~300), document_files (~70),
    messages (~1500), feedbacks (~700), activities (~250), student_access_flag (1)

A small set of **curated accounts keeps stable logins** for manual testing:
    admin / admin123            superadmin / admin123
    hoda_dr|khaled_dr|noha_dr|tarek_dr / instructor123
    student / student123        nour_s|omar_s|aya_s|ahmed_s|mariam_s / student123

Instructor roles per subject (InstructorSubjectRole):
    SUPER  — owns the subject; can upload/delete materials and manage roster.
    VIEWER — read-only; can view materials and analytics but cannot modify.
Each subject_instructor row carries an explicit ``instructor_role`` field.
Exactly one SUPER per subject is enforced by a partial unique index.

Tweak the volume knobs in the "Generation knobs" section below to scale up/down.

Each run **truncates** all seeded tables and inserts fresh rows from this file.
Because generation is deterministic, every run produces the *same* dataset
(same ids, passwords, enrollments), so the database stays reproducible.
"""
from __future__ import annotations

import asyncio
import os
import random
import sys
from datetime import date, datetime, timedelta, timezone

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
from db.models.subject_instructor import InstructorSubjectRole, SubjectInstructor
from db.models.subject_student import SubjectStudent
from db.models.system_flag import StudentAccessFlag
from db.models.user import User, UserRole, UserStatus, _new_user_id
from helpers.auth import hash_password
from helpers.config import get_settings

_NOW = datetime.now(timezone.utc)
_RND = random.Random(20260620)  # fixed seed → fully reproducible dataset


def _ago(days: int = 0, hours: int = 0) -> datetime:
    return _NOW - timedelta(days=days, hours=hours)


def _rand_dt(min_days_ago: int, max_days_ago: int) -> datetime:
    """A random UTC datetime between ``min_days_ago`` and ``max_days_ago`` days back."""
    lo, hi = min(min_days_ago, max_days_ago), max(min_days_ago, max_days_ago)
    days = _RND.randint(lo, hi)
    return _NOW - timedelta(days=days, seconds=_RND.randint(0, 86_399))


# ---------------------------------------------------------------------------
# Generation knobs — bump these to scale the dataset up or down
# ---------------------------------------------------------------------------

_N_INSTRUCTORS = 20          # total instructors (incl. curated)
_N_STUDENTS = 90             # total students (incl. curated)
_SUBJECTS_PER_SEMESTER = (5, 8)        # min/max subjects generated per semester
_ENROLLMENT_PER_SUBJECT = (10, 32)     # min/max students enrolled per subject
_MATERIALS_PER_SUBJECT = (4, 14)       # min/max materials per subject
_CONVS_PER_STUDENT = (1, 6)            # tutor/doc conversations per student
_TURNS_PER_CONV = (1, 5)               # user+assistant message pairs per conversation

_S = InstructorSubjectRole.SUPER
_V = InstructorSubjectRole.VIEWER


# ---------------------------------------------------------------------------
# Name / content pools (used by the generators below)
# ---------------------------------------------------------------------------

_FIRST_NAMES = [
    "Ahmed", "Mohamed", "Mahmoud", "Mostafa", "Omar", "Khaled", "Tarek", "Hassan",
    "Hussein", "Youssef", "Karim", "Amr", "Sherif", "Ramy", "Sameh", "Hany",
    "Ali", "Kareem", "Ziad", "Adham", "Seif", "Marwan", "Bassel", "Fady",
    "Nour", "Aya", "Mariam", "Noha", "Hoda", "Salma", "Sara", "Yasmin",
    "Dina", "Mona", "Rana", "Heba", "Asmaa", "Fatma", "Esraa", "Menna",
    "Reem", "Habiba", "Farida", "Malak", "Layla", "Nada", "Ola", "Doaa",
]

_LAST_NAMES = [
    "Mahmoud", "Abdel-Aziz", "Farouk", "El-Sayed", "Hassan", "Salah", "Ibrahim",
    "Mostafa", "Youssef", "Ali", "Mohamed", "Saleh", "Fathy", "Gomaa", "Mansour",
    "Nasser", "Shawky", "Zaki", "Fahmy", "Sabry", "Rashad", "Hamdy", "Kamal",
    "Lotfy", "Ezzat", "Selim", "Helmy", "Galal", "Sami", "Wagdy", "Habib",
    "Sharaf", "Tawfik", "Saad", "Refaat", "Adel", "Sobhy", "Ramadan", "Bakr",
]

# (course_code, title, description) — drawn from to build subjects.
_COURSE_CATALOG = [
    ("CS101", "Introduction to Computer Science", "Fundamentals of programming, algorithms, and computational thinking."),
    ("CS102", "Programming Fundamentals II",      "Object-oriented programming, recursion, and modular design."),
    ("CS201", "Data Structures & Algorithms",     "Arrays, linked lists, trees, graphs, sorting, and search algorithms."),
    ("CS202", "Operating Systems",                "Processes, threads, memory management, file systems, and I/O."),
    ("CS210", "Discrete Mathematics",             "Logic, sets, relations, combinatorics, and graph theory."),
    ("CS301", "Database Systems",                 "Relational models, SQL, transactions, normalization, and query optimization."),
    ("CS305", "Computer Networks",                "OSI model, TCP/IP, routing, network security, and distributed systems."),
    ("CS310", "Software Engineering",             "SDLC, design patterns, testing, CI/CD, and agile methodologies."),
    ("CS320", "Web Development",                  "HTTP, REST APIs, front-end frameworks, and full-stack architecture."),
    ("CS330", "Mobile App Development",           "Cross-platform mobile apps, state management, and device APIs."),
    ("CS340", "Compilers",                        "Lexical analysis, parsing, semantic analysis, and code generation."),
    ("CS350", "Cybersecurity",                    "Cryptography, authentication, threat modeling, and secure coding."),
    ("CS360", "Cloud Computing",                  "Virtualization, containers, orchestration, and serverless platforms."),
    ("CS401", "Machine Learning",                 "Supervised and unsupervised learning, neural networks, and model evaluation."),
    ("CS402", "Natural Language Processing",      "Text processing, language models, transformers, and NLP applications."),
    ("CS410", "Computer Vision",                  "Image processing, convolutional networks, object detection, and segmentation."),
    ("CS420", "Deep Learning",                    "Optimization, CNNs, RNNs, attention, and generative models."),
    ("CS430", "Reinforcement Learning",           "Markov decision processes, Q-learning, and policy gradients."),
    ("CS440", "Big Data Systems",                 "Distributed storage, MapReduce, streaming, and data pipelines."),
    ("CS450", "Distributed Systems",              "Consensus, replication, fault tolerance, and CAP theorem."),
    ("MATH201", "Linear Algebra",                 "Vectors, matrices, eigenvalues, and applications in data science."),
    ("MATH202", "Calculus III",                   "Multivariable calculus, gradients, and vector fields."),
    ("MATH301", "Probability & Statistics",       "Probability theory, distributions, hypothesis testing, and regression."),
    ("MATH310", "Numerical Methods",              "Root finding, interpolation, numerical integration, and stability."),
]

# (extension, mime) pairs used for materials & uploaded files.
_FILE_TYPES = [
    (".pdf",  "application/pdf"),
    (".pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
    (".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    (".pdf",  "application/pdf"),  # weight PDFs a bit heavier
]

_MATERIAL_TOPICS = [
    "Lecture {n} - Introduction", "Lecture {n} - Core Concepts", "Lecture {n} - Advanced Topics",
    "Week {n} Slides", "Week {n} Lab", "Tutorial {n}", "Assignment {n} Brief",
    "Chapter {n} Notes", "Practice Problems {n}", "Case Study {n}",
    "Review Session {n}", "Reference Sheet {n}", "Project Guidelines {n}",
]

# (user_q, assistant_reply) — generic tutor/doc exchanges sampled per conversation.
_MESSAGE_PAIRS = [
    ("Can you explain for loops?",                        "Sure! A for loop iterates over a sequence. For example: `for i in range(10): print(i)` prints 0 through 9."),
    ("What is the difference between a stack and queue?", "A stack is LIFO (Last In First Out), while a queue is FIFO (First In First Out). Stacks use push/pop; queues use enqueue/dequeue."),
    ("How do I write a LEFT JOIN?",                       "A LEFT JOIN returns all rows from the left table and matched rows from the right. Example: `SELECT * FROM a LEFT JOIN b ON a.id = b.a_id`."),
    ("Summarise the document for me.",                    "The document covers three main topics: introduction to neural networks, backpropagation, and regularisation techniques. Let me know which part to expand on."),
    ("How does gradient descent work?",                   "Gradient descent minimises a loss function by iteratively moving in the direction of the negative gradient. The learning rate controls the step size."),
    ("What does this paper say about attention?",         "The paper introduces self-attention, which lets each token attend to all other tokens, replacing recurrence with parallelisable matrix operations."),
    ("Prove that A is an eigenvalue.",                    "An eigenvalue λ satisfies det(A - λI) = 0. Solving this characteristic polynomial gives you the eigenvalues of matrix A."),
    ("What is a process vs a thread?",                    "A process has its own memory space; threads share memory within a process. Threads are lighter and faster to create, but require synchronisation."),
    ("Explain the TCP three-way handshake.",              "Step 1: Client sends SYN. Step 2: Server replies SYN-ACK. Step 3: Client sends ACK. After this the connection is established."),
    ("Summarise these lecture slides.",                   "The slides cover: (1) OSI model layers, (2) IP addressing and subnetting, and (3) routing protocols including OSPF and BGP."),
    ("What is a transformer model?",                      "A transformer uses self-attention and feed-forward layers arranged in an encoder-decoder structure. It processes sequences in parallel, unlike RNNs."),
    ("What is Bayes' theorem?",                           "Bayes' theorem: P(A|B) = P(B|A)·P(A) / P(B). It updates the probability of A given new evidence B."),
    ("Can you give me a worked example?",                 "Of course. Let's walk through it step by step with concrete numbers so the intuition is clear before we generalise."),
    ("Why is my recursion not terminating?",              "Most likely your base case is never reached. Make sure every recursive call moves strictly toward the base condition."),
    ("What's the time complexity here?",                  "This runs in O(n log n): the sort dominates, and the subsequent linear scan is O(n), which is absorbed into the larger term."),
    ("How do I normalise this table?",                    "Start with 1NF (atomic columns), then 2NF (remove partial dependencies), then 3NF (remove transitive dependencies on the key)."),
]

_CONV_TITLES_TUTOR = [
    "Help with {topic}", "{topic} question", "Stuck on {topic}", "Understanding {topic}",
    "{topic} practice", "Quick question about {topic}", "Exam revision: {topic}",
]
_CONV_TITLES_DOC = [
    "Lecture notes summary", "Paper review", "Reading summary", "Assignment draft review",
    "Slides Q&A", "Research notes", "Textbook chapter summary",
]
_CONV_TOPICS = [
    "loops", "recursion", "binary trees", "SQL joins", "gradient descent", "eigenvalues",
    "scheduling", "TCP handshake", "attention", "Bayesian inference", "normalisation",
    "pointers", "hash maps", "dynamic programming", "graph traversal", "backpropagation",
]


# ---------------------------------------------------------------------------
# Generators — build the seed specs procedurally
# ---------------------------------------------------------------------------

def _semester_short(sem_id: str) -> str:
    term, year = sem_id.split("-")
    return ("f" if term == "fall" else "sp") + year[2:]


def _semester_start(sem_id: str) -> datetime:
    term, year = sem_id.split("-")
    month = 9 if term == "fall" else 2
    return datetime(int(year), month, 1, tzinfo=timezone.utc)


def _semester_end(sem_id: str) -> date:
    """End date = the day before the next term starts (contiguous, no gaps).

    Contiguity guarantees the term containing ``_NOW`` always resolves to
    ``active`` under ``derive_semester_state`` — there is no inter-term gap for a
    seed run to fall into, so a fresh dataset always has a current semester.
    """
    term, year = sem_id.split("-")
    y = int(year)
    if term == "fall":
        return date(y + 1, 2, 1) - timedelta(days=1)  # → Jan 31 next year
    return date(y, 9, 1) - timedelta(days=1)  # spring → Aug 31


def _semester_anchor_days_ago(sem_id: str) -> int:
    """Approx days-ago for the *start* of a semester, used to age its content."""
    return max((_NOW - _semester_start(sem_id)).days, 1)


def _build_semesters() -> list[dict]:
    sems: list[dict] = []
    order = 1
    for year in (2023, 2024, 2025, 2026):
        for term in ("spring", "fall"):
            sem_id = f"{term}-{year}"
            # Keep everything in the past relative to _NOW (skip future terms).
            if _semester_start(sem_id) >= _NOW:
                continue
            sems.append({
                "id": sem_id,
                "label": f"{term.capitalize()} {year}",
                "sort_order": order,
                "start_date": _semester_start(sem_id).date(),
                "end_date": _semester_end(sem_id),
            })
            order += 1
    return sems


def _build_users() -> tuple[list[dict], list[str], list[str]]:
    """Returns (user_specs, instructor_usernames, student_usernames)."""
    curated = [
        {"username": "admin",      "name": "System Admin", "email": "admin@docmind.local",      "role": UserRole.ADMIN,      "password": "admin123"},
        {"username": "superadmin", "name": "Super Admin",  "email": "superadmin@docmind.local", "role": UserRole.ADMIN,      "password": "admin123"},
        {"username": "hoda_dr",    "name": "Dr. Hoda Mahmoud",      "email": "hoda@docmind.local",   "role": UserRole.INSTRUCTOR, "password": "instructor123"},
        {"username": "khaled_dr",  "name": "Dr. Khaled Abdel-Aziz", "email": "khaled@docmind.local", "role": UserRole.INSTRUCTOR, "password": "instructor123"},
        {"username": "noha_dr",    "name": "Dr. Noha Farouk",       "email": "noha@docmind.local",   "role": UserRole.INSTRUCTOR, "password": "instructor123"},
        {"username": "tarek_dr",   "name": "Dr. Tarek El-Sayed",    "email": "tarek@docmind.local",  "role": UserRole.INSTRUCTOR, "password": "instructor123"},
        {"username": "student",    "name": "Demo Student",   "email": "student@docmind.local", "role": UserRole.STUDENT, "password": "student123"},
        {"username": "nour_s",     "name": "Nour Hassan",    "email": "nour@docmind.local",    "role": UserRole.STUDENT, "password": "student123"},
        {"username": "omar_s",     "name": "Omar Salah",     "email": "omar@docmind.local",    "role": UserRole.STUDENT, "password": "student123"},
        {"username": "aya_s",      "name": "Aya Ibrahim",    "email": "aya@docmind.local",     "role": UserRole.STUDENT, "password": "student123"},
        {"username": "ahmed_s",    "name": "Ahmed Mostafa",  "email": "ahmed@docmind.local",   "role": UserRole.STUDENT, "password": "student123"},
        {"username": "mariam_s",   "name": "Mariam Youssef", "email": "mariam@docmind.local",  "role": UserRole.STUDENT, "password": "student123"},
    ]

    users: list[dict] = []
    used_usernames: set[str] = set()
    used_emails: set[str] = set()

    instructor_usernames: list[str] = []
    student_usernames: list[str] = []

    def _add(spec: dict) -> None:
        used_usernames.add(spec["username"])
        used_emails.add(spec["email"])
        users.append(spec)
        if spec["role"] == UserRole.INSTRUCTOR:
            instructor_usernames.append(spec["username"])
        elif spec["role"] == UserRole.STUDENT:
            student_usernames.append(spec["username"])

    for spec in curated:
        spec = dict(spec)
        spec["registered_at"] = _rand_dt(540, 730)
        spec["last_active"] = _rand_dt(0, 20)
        spec["status"] = UserStatus.ACTIVE
        _add(spec)

    def _unique_username(first: str, last: str) -> str:
        base = f"{first}.{last}".lower().replace("-", "")
        candidate = base
        n = 1
        while candidate in used_usernames:
            n += 1
            candidate = f"{base}{n}"
        return candidate

    n_more_instr = max(_N_INSTRUCTORS - len(instructor_usernames), 0)
    for _ in range(n_more_instr):
        first = _RND.choice(_FIRST_NAMES)
        last = _RND.choice(_LAST_NAMES)
        uname = _unique_username(first, last)
        _add({
            "username": uname,
            "name": f"Dr. {first} {last}",
            "email": f"{uname}@docmind.local",
            "role": UserRole.INSTRUCTOR,
            "password": "instructor123",
            "registered_at": _rand_dt(365, 900),
            "last_active": (None if _RND.random() < 0.1 else _rand_dt(0, 40)),
            "status": UserStatus.ACTIVE,
        })

    n_more_students = max(_N_STUDENTS - len(student_usernames), 0)
    for _ in range(n_more_students):
        first = _RND.choice(_FIRST_NAMES)
        last = _RND.choice(_LAST_NAMES)
        uname = _unique_username(first, last)
        # ~6% of students are disabled, ~12% never logged in (no last_active).
        disabled = _RND.random() < 0.06
        _add({
            "username": uname,
            "name": f"{first} {last}",
            "email": f"{uname}@docmind.local",
            "role": UserRole.STUDENT,
            "password": "student123",
            "registered_at": _rand_dt(10, 700),
            "last_active": (None if (disabled or _RND.random() < 0.12) else _rand_dt(0, 60)),
            "status": UserStatus.DISABLED if disabled else UserStatus.ACTIVE,
        })

    return users, instructor_usernames, student_usernames


def _build_subjects(
    semesters: list[dict],
    instructor_usernames: list[str],
    student_usernames: list[str],
) -> list[dict]:
    subjects: list[dict] = []
    used_ids: set[str] = set()

    for sem in semesters:
        sem_id = sem["id"]
        short = _semester_short(sem_id)
        anchor = _semester_anchor_days_ago(sem_id)
        n = _RND.randint(*_SUBJECTS_PER_SEMESTER)
        courses = _RND.sample(_COURSE_CATALOG, min(n, len(_COURSE_CATALOG)))
        for code, title, desc in courses:
            sid = f"{code.lower()}-{short}"
            if sid in used_ids:
                continue
            used_ids.add(sid)

            # One SUPER + 0..2 VIEWERs, all distinct.
            roster = _RND.sample(
                instructor_usernames,
                min(len(instructor_usernames), 1 + _RND.randint(0, 2)),
            )
            instructors = [(roster[0], _S)] + [(u, _V) for u in roster[1:]]

            enroll_n = min(len(student_usernames), _RND.randint(*_ENROLLMENT_PER_SUBJECT))
            students = _RND.sample(student_usernames, enroll_n)

            subjects.append({
                "id": sid,
                "title": title,
                "description": desc,
                "course_code": code,
                "semester_id": sem_id,
                "instructors": instructors,
                "students": students,
                "created_at": _rand_dt(anchor, anchor + 14),
            })

    # Guarantee the curated demo accounts have plenty of data to browse.
    _ensure_min_enrollment(subjects, "student", minimum=6)
    for uname in ("nour_s", "omar_s", "aya_s", "ahmed_s", "mariam_s"):
        _ensure_min_enrollment(subjects, uname, minimum=4)

    return subjects


def _ensure_min_enrollment(subjects: list[dict], username: str, minimum: int) -> None:
    enrolled = [s for s in subjects if username in s["students"]]
    if len(enrolled) >= minimum:
        return
    candidates = [s for s in subjects if username not in s["students"]]
    _RND.shuffle(candidates)
    for subj in candidates[: minimum - len(enrolled)]:
        subj["students"].append(username)


def _build_materials(subjects: list[dict]) -> list[dict]:
    materials: list[dict] = []
    for subj in subjects:
        sid = subj["id"]
        anchor = _semester_anchor_days_ago(subj["semester_id"])
        # Only the super instructor may upload — match MaterialService policy.
        super_instructor = next(u for u, role in subj["instructors"] if role == _S)
        count = _RND.randint(*_MATERIALS_PER_SUBJECT)
        for n in range(1, count + 1):
            ext, mime = _RND.choice(_FILE_TYPES)
            topic = _RND.choice(_MATERIAL_TOPICS).format(n=n)
            # Most processed; a few still indexing or failed for realistic states.
            roll = _RND.random()
            if roll < 0.85:
                status = MaterialStatus.PROCESSED
            elif roll < 0.95:
                status = MaterialStatus.INDEXING
            else:
                status = MaterialStatus.FAILED
            materials.append({
                "subject_id": sid,
                "name": f"{topic}{ext}",
                "size_bytes": _RND.randint(120, 9_500) * 1_000,
                "mime": mime,
                "storage_path": f"materials/{sid}/{n:02d}-{topic.lower().replace(' ', '_')}{ext}",
                "status": status,
                "uploaded_by": super_instructor,
                "created_at": _rand_dt(max(anchor - count, 1), anchor + 10),
            })
    return materials


def _build_conversations(subjects: list[dict], student_usernames: list[str]) -> list[dict]:
    # Map each student → subjects they're enrolled in (for tutor-chat context).
    by_student: dict[str, list[dict]] = {u: [] for u in student_usernames}
    for subj in subjects:
        for u in subj["students"]:
            if u in by_student:
                by_student[u].append(subj)

    conversations: list[dict] = []
    for uname in student_usernames:
        enrolled = by_student[uname]
        n_conv = _RND.randint(*_CONVS_PER_STUDENT)
        for _ in range(n_conv):
            is_doc = _RND.random() < 0.3 or not enrolled
            base_dt = _rand_dt(0, 120)

            if is_doc:
                kind = ConversationKind.DOC
                subject_id = None
                title = _RND.choice(_CONV_TITLES_DOC)
                file_spec = _build_doc_file(base_dt)
            else:
                kind = ConversationKind.TUTOR
                subj = _RND.choice(enrolled)
                subject_id = subj["id"]
                title = _RND.choice(_CONV_TITLES_TUTOR).format(topic=_RND.choice(_CONV_TOPICS))
                file_spec = None

            turns = []
            ts = base_dt
            for _t in range(_RND.randint(*_TURNS_PER_CONV)):
                q, a = _RND.choice(_MESSAGE_PAIRS)
                # ~55% of assistant replies get up/down feedback.
                if _RND.random() < 0.55:
                    feedback = FeedbackValue.UP if _RND.random() < 0.78 else FeedbackValue.DOWN
                else:
                    feedback = None
                turns.append({"q": q, "a": a, "ts": ts, "feedback": feedback})
                ts = ts + timedelta(minutes=_RND.randint(1, 90))

            conversations.append({
                "owner": uname,
                "kind": kind,
                "subject_id": subject_id,
                "title": title,
                "created_at": base_dt,
                "file": file_spec,
                "turns": turns,
            })
    return conversations


def _build_doc_file(base_dt: datetime) -> dict:
    ext, mime = _RND.choice(_FILE_TYPES)
    roll = _RND.random()
    if roll < 0.88:
        status = DocumentFileStatus.READY
    elif roll < 0.96:
        status = DocumentFileStatus.PROCESSING
    else:
        status = DocumentFileStatus.FAILED
    return {
        "name": f"uploaded_doc{ext}",
        "size_bytes": _RND.randint(80, 6_000) * 1_000,
        "mime": mime,
        "status": status,
        "created_at": base_dt,
    }


def _build_activities(
    users: list[dict],
    subjects: list[dict],
    materials: list[dict],
) -> list[dict]:
    """Build an admin activity feed referencing real generated entities."""
    activities: list[dict] = []
    admins = [u["username"] for u in users if u["role"] == UserRole.ADMIN] or ["admin"]

    def _label_for(subj: dict) -> str:
        return f"{subj['course_code']} {subj['semester_id'].replace('-', ' ').title()}"

    # Account creation events for instructors + a sample of students.
    instr = [u for u in users if u["role"] == UserRole.INSTRUCTOR]
    sample_students = _RND.sample(
        [u for u in users if u["role"] == UserRole.STUDENT],
        min(40, sum(u["role"] == UserRole.STUDENT for u in users)),
    )
    for u in instr + sample_students:
        activities.append({
            "actor": _RND.choice(admins),
            "action": f"Created user '{u['username']}'",
            "label": u["name"],
            "meta": {"role": u["role"].value},
            "created_at": u.get("registered_at") or _rand_dt(200, 700),
        })

    # Subject creation + instructor assignment events.
    for subj in subjects:
        activities.append({
            "actor": _RND.choice(admins),
            "action": f"Created subject '{subj['id']}'",
            "label": _label_for(subj),
            "meta": {"course_code": subj["course_code"]},
            "created_at": subj["created_at"],
        })
        for uname, role in subj["instructors"]:
            verb = "super instructor" if role == _S else "viewer"
            activities.append({
                "actor": _RND.choice(admins),
                "action": f"Assigned {uname} as {verb} of {subj['id']}",
                "label": _label_for(subj),
                "meta": {"instructor": uname, "instructor_role": role.value},
                "created_at": subj["created_at"] + timedelta(hours=_RND.randint(1, 48)),
            })

    # Material upload events (sample to keep the feed readable).
    for mat in _RND.sample(materials, min(60, len(materials))):
        activities.append({
            "actor": mat["uploaded_by"],
            "action": f"Uploaded material '{mat['name']}'",
            "label": mat["subject_id"],
            "meta": {"size_bytes": mat["size_bytes"]},
            "created_at": mat["created_at"],
        })

    # A few global student-access toggles.
    for enabled, note, days in [
        (True, "Enabled student access", 400),
        (False, "Disabled student access for maintenance", 120),
        (True, "Re-enabled student access", 119),
        (False, "Disabled student access during exams", 45),
        (True, "Re-enabled student access after exams", 30),
    ]:
        activities.append({
            "actor": _RND.choice(admins),
            "action": note,
            "label": None,
            "meta": {"enabled": enabled},
            "created_at": _rand_dt(days, days),
        })

    activities.sort(key=lambda a: a["created_at"])
    return activities


# ---------------------------------------------------------------------------
# Materialise the generated specs (module-level, deterministic)
# ---------------------------------------------------------------------------

_SEMESTERS = _build_semesters()
_USERS, _INSTRUCTOR_USERNAMES, _STUDENT_USERNAMES = _build_users()
_SUBJECTS = _build_subjects(_SEMESTERS, _INSTRUCTOR_USERNAMES, _STUDENT_USERNAMES)
_MATERIAL_SPECS = _build_materials(_SUBJECTS)
_CONVERSATIONS = _build_conversations(_SUBJECTS, _STUDENT_USERNAMES)
_ACTIVITY_SPECS = _build_activities(_USERS, _SUBJECTS, _MATERIAL_SPECS)


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
        registered_at = spec.get("registered_at") or _ago(days=60)
        session.add(User(
            id=uid,
            username=spec["username"],
            name=spec["name"],
            email=spec["email"],
            role=spec["role"],
            status=spec.get("status", UserStatus.ACTIVE),
            password_hash=hash_password(spec["password"]),
            registered_at=registered_at,
            last_active=spec.get("last_active"),
            created_at=registered_at,
            updated_at=spec.get("last_active") or registered_at,
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
            created_at = spec.get("created_at") or _ago(days=120)
            session.add(Subject(
                id=sid,
                title=spec["title"],
                description=spec["description"],
                course_code=spec["course_code"],
                semester_id=spec["semester_id"],
                created_at=created_at,
                updated_at=created_at,
            ))
            _log("insert", f"subject '{sid}'")

        # subject_instructors — roles are explicit in _SUBJECTS data.
        for uname, role in spec["instructors"]:
            uid = uid_map.get(uname)
            if not uid:
                continue
            existing = await session.get(SubjectInstructor, {"subject_id": sid, "user_id": uid})
            if existing:
                continue
            session.add(SubjectInstructor(subject_id=sid, user_id=uid, instructor_role=role))
            _log("insert", f"  subject_instructor {sid} <- {uname} ({role.value})")

        # subject_students (composite PK — safe to re-insert)
        for uname in spec.get("students", []):
            uid = uid_map.get(uname)
            if not uid:
                continue
            existing = await session.get(SubjectStudent, {"subject_id": sid, "user_id": uid})
            if existing:
                continue
            session.add(SubjectStudent(subject_id=sid, user_id=uid))
            _log("insert", f"  subject_student    {sid} <- {uname}")

    await session.flush()


async def _seed_materials(session: AsyncSession, uid_map: dict[str, str]) -> None:
    for i, spec in enumerate(_MATERIAL_SPECS):
        exists = await session.scalar(
            select(Material).where(Material.storage_path == spec["storage_path"])
        )
        if exists:
            continue
        created_at = spec.get("created_at") or _ago(days=90)
        session.add(Material(
            id=_new_material_id(),
            subject_id=spec["subject_id"],
            name=spec["name"],
            size_bytes=spec["size_bytes"],
            mime=spec["mime"],
            storage_path=spec["storage_path"],
            status=spec["status"],
            uploaded_by_id=uid_map.get(spec["uploaded_by"]),
            created_at=created_at,
            updated_at=created_at,
        ))
        if (i + 1) % 50 == 0:
            _log("insert", f"materials … {i + 1}/{len(_MATERIAL_SPECS)}")
    _log("insert", f"materials total: {len(_MATERIAL_SPECS)}")
    await session.flush()


async def _seed_conversations_and_messages(
    session: AsyncSession, uid_map: dict[str, str]
) -> None:
    n_conv = n_msg = n_file = n_fb = 0
    for spec in _CONVERSATIONS:
        owner_id = uid_map.get(spec["owner"])
        if not owner_id:
            continue

        kind = spec["kind"]
        conv_created = spec["created_at"]
        # updated_at tracks the last message timestamp for realistic recency sorting.
        last_ts = spec["turns"][-1]["ts"] if spec["turns"] else conv_created

        conv_id = _new_conv_id()
        session.add(Conversation(
            id=conv_id,
            owner_id=owner_id,
            kind=kind,
            subject_id=spec["subject_id"],
            title=spec["title"],
            created_at=conv_created,
            updated_at=last_ts,
        ))
        n_conv += 1
        await session.flush()

        file_spec = spec.get("file")
        if kind == ConversationKind.DOC and file_spec:
            session.add(DocumentFile(
                id=_new_file_id(),
                conversation_id=conv_id,
                name=file_spec["name"],
                size_bytes=file_spec["size_bytes"],
                mime=file_spec["mime"],
                storage_path=f"doc_uploads/{conv_id}/{file_spec['name']}",
                status=file_spec["status"],
                created_at=file_spec["created_at"],
                updated_at=file_spec["created_at"],
            ))
            n_file += 1

        asst_role = MessageRole.DOC if kind == ConversationKind.DOC else MessageRole.ASSISTANT
        for turn in spec["turns"]:
            user_ts = turn["ts"]
            asst_ts = user_ts + timedelta(seconds=_RND.randint(3, 90))
            user_msg_id = _new_message_id()
            asst_msg_id = _new_message_id()
            session.add(Message(
                id=user_msg_id, conversation_id=conv_id, role=MessageRole.USER,
                text=turn["q"], created_at=user_ts, updated_at=user_ts,
            ))
            session.add(Message(
                id=asst_msg_id, conversation_id=conv_id, role=asst_role,
                text=turn["a"], created_at=asst_ts, updated_at=asst_ts,
            ))
            n_msg += 2
            await session.flush()

            if turn["feedback"] is not None:
                session.add(Feedback(
                    id=_new_feedback_id(),
                    message_id=asst_msg_id,
                    user_id=owner_id,
                    feedback=turn["feedback"],
                    created_at=asst_ts,
                    updated_at=asst_ts,
                ))
                n_fb += 1

        if n_conv % 50 == 0:
            _log("insert", f"conversations … {n_conv}/{len(_CONVERSATIONS)}")

    _log("insert", f"conversations: {n_conv}, messages: {n_msg}, files: {n_file}, feedbacks: {n_fb}")
    await session.flush()


async def _seed_activities(session: AsyncSession, uid_map: dict[str, str]) -> None:
    existing_count = await session.scalar(
        select(Activity).where(Activity.action.ilike("Created user%"))
    )
    if existing_count:
        _log("skip", "activities (already seeded)")
        return
    for spec in _ACTIVITY_SPECS:
        created_at = spec.get("created_at") or _ago(days=30)
        session.add(Activity(
            id=_new_activity_id(),
            action=spec["action"],
            actor_user_id=uid_map.get(spec["actor"]),
            subject_label=spec["label"],
            meta=spec["meta"],
            created_at=created_at,
            updated_at=created_at,
        ))
    _log("insert", f"activities total: {len(_ACTIVITY_SPECS)}")
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
        print("\n--- Wipe ---")
        await _wipe_all(session)

        print("\n--- Users ---")
        uid_map = await _seed_users(session)

        print("\n--- Semesters ---")
        await _seed_semesters(session)

        print("\n--- Subjects & Instructors ---")
        await _seed_subjects(session, uid_map)

        print("\n--- Materials ---")
        await _seed_materials(session, uid_map)

        print("\n--- Conversations, Files, Messages, Feedbacks ---")
        await _seed_conversations_and_messages(session, uid_map)

        print("\n--- Activities ---")
        await _seed_activities(session, uid_map)

        print("\n--- System Flags ---")
        await _seed_student_access_flag(session)

        await session.commit()

    await engine.dispose()
    print("\nSeed complete.\n")


if __name__ == "__main__":
    asyncio.run(main())
