"""Pytest harness for DocMind backend integration tests.

- Real Postgres + pgvector (schema via ``alembic upgrade head``), faked LLM /
  vector providers, agent disabled.
- Each test runs against a freshly-truncated DB; fixtures seed only what they need.
- The app is driven through ``httpx.AsyncClient(ASGITransport)`` which does NOT
  fire Starlette startup, so we inject providers/session-maker onto ``app.state``.

Requires a running Postgres+pgvector. Default target:
``postgresql+asyncpg://admin:pass123@localhost:5433/docmind_test`` (override with
the ``TEST_DATABASE_URL`` env var). The DB is created + migrated automatically.
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

SRC_DIR = Path(__file__).resolve().parent.parent

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://admin:pass123@localhost:5433/docmind_test",
)


def _sync_url(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://")


def _split_url(url: str) -> dict:
    # postgresql+asyncpg://user:pass@host:port/dbname
    rest = url.split("://", 1)[1]
    creds, hostpart = rest.split("@", 1)
    user, password = creds.split(":", 1)
    hostport, dbname = hostpart.split("/", 1)
    host, port = hostport.split(":", 1)
    return {"user": user, "password": password, "host": host, "port": int(port), "database": dbname}


async def _ensure_database() -> None:
    """Create the test database if it does not yet exist (best-effort)."""
    parts = _split_url(TEST_DATABASE_URL)
    dbname = parts.pop("database")
    for maintenance in ("postgres", "template1", "mini_rag"):
        try:
            conn = await asyncpg.connect(database=maintenance, **parts)
        except Exception:
            continue
        try:
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname=$1", dbname
            )
            if not exists:
                await conn.execute(f'CREATE DATABASE "{dbname}"')
        finally:
            await conn.close()
        return
    raise RuntimeError("Could not connect to a maintenance database to create the test DB")


@pytest.fixture(scope="session", autouse=True)
def _schema() -> None:
    """Ensure the test DB exists and is migrated to head (once per session)."""
    asyncio.new_event_loop().run_until_complete(_ensure_database())
    env = {**os.environ, "DATABASE_URL": _sync_url(TEST_DATABASE_URL)}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(SRC_DIR),
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"alembic upgrade head failed:\n{result.stdout}\n{result.stderr}")


@pytest_asyncio.fixture
async def engine(_schema):
    """Fresh async engine per test (avoids cross-event-loop asyncpg issues).

    On setup it truncates every ORM table so each test starts from a clean slate.
    """
    from db.base import Base
    from db import models  # noqa: F401 -- registers all tables on Base.metadata
    from db.session import create_engine_and_sessionmaker

    eng, _factory = create_engine_and_sessionmaker(TEST_DATABASE_URL)
    table_names = ", ".join(t.name for t in Base.metadata.sorted_tables)
    async with eng.begin() as conn:
        await conn.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_maker(engine):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    return async_sessionmaker(
        bind=engine, expire_on_commit=False, autoflush=False, class_=AsyncSession
    )


@pytest_asyncio.fixture
async def db(session_maker):
    """Direct test-side session for seeding rows (commits make them app-visible)."""
    async with session_maker() as session:
        yield session


@pytest.fixture
def app(session_maker):
    """The real FastAPI app with test session-maker + faked providers on app.state."""
    from main import app as fastapi_app
    from stores.llm.templates.TemplateParser import TemplateParser

    from tests.fakes import FakeLLM, FakeVectorDB

    fake_llm = FakeLLM()
    fastapi_app.state.session_maker = session_maker
    fastapi_app.state.embedding_client = fake_llm
    fastapi_app.state.generation_client = fake_llm
    fastapi_app.state.vectordb_client = FakeVectorDB()
    fastapi_app.state.template_parser = TemplateParser(language="en")
    fastapi_app.state.agent_client = None
    return fastapi_app


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# --------------------------------------------------------------------------- #
# Auth helpers
# --------------------------------------------------------------------------- #

def auth_header(user) -> dict:
    """Bearer header for a User (reuses the app's own token signing)."""
    from helpers.auth import create_access_token

    token, _jti, _exp = create_access_token(sub=user.id, role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------- #
# Seeder — build valid domain rows through the same code paths the app uses
# --------------------------------------------------------------------------- #

class Seeder:
    def __init__(self, session):
        self.s = session

    async def user(self, role, *, username=None, password="pw123456", status=None, **over):
        from db.models import User, UserRole, UserStatus
        from helpers.auth import hash_password
        from repositories.user_repository import UserRepository

        role = role if isinstance(role, UserRole) else UserRole(role)
        n = username or f"{role.value}_{os.urandom(3).hex()}"
        user = User(
            username=n,
            name=over.pop("name", n.replace("_", " ").title()),
            email=over.pop("email", f"{n}@test.local"),
            role=role,
            status=status or UserStatus.ACTIVE,
            password_hash=hash_password(password),
            registered_at=datetime.now(timezone.utc),
            **over,
        )
        await UserRepository(self.s).add(user)
        await self.s.commit()
        return user

    async def admin(self, **kw):
        from db.models import UserRole
        return await self.user(UserRole.ADMIN, **kw)

    async def instructor(self, **kw):
        from db.models import UserRole
        return await self.user(UserRole.INSTRUCTOR, **kw)

    async def student(self, **kw):
        from db.models import UserRole
        return await self.user(UserRole.STUDENT, **kw)

    async def semester(
        self, *, id="sem-test", label="Test Semester", sort_order=0,
        start_date=None, end_date=None,
    ):
        from db.models import Semester
        sem = Semester(
            id=id, label=label, sort_order=sort_order,
            start_date=start_date, end_date=end_date,
        )
        self.s.add(sem)
        await self.s.commit()
        return sem

    async def subject(
        self,
        *,
        id="sub-test",
        title="Test Subject",
        description="A subject for tests.",
        course_code="TST101",
        semester_id=None,
        instructors=(),
        super_id=None,
        students=(),
    ):
        from db.models import Subject
        from repositories.subject_repository import SubjectRepository

        repo = SubjectRepository(self.s)
        subject = Subject(
            id=id, title=title, description=description,
            course_code=course_code, semester_id=semester_id,
        )
        await repo.add(subject)
        instructor_ids = [u.id if hasattr(u, "id") else u for u in instructors]
        student_ids = [u.id if hasattr(u, "id") else u for u in students]
        if instructor_ids:
            chosen_super = super_id.id if hasattr(super_id, "id") else (super_id or instructor_ids[0])
            await repo.replace_instructors(subject.id, instructor_ids, chosen_super)
        if student_ids:
            await repo.replace_students(subject.id, student_ids)
        await self.s.commit()
        return subject

    async def material(self, subject_id, *, status=None, uploaded_by_id=None, name="Lecture 1"):
        from db.models import Material, MaterialStatus
        from repositories.material_repository import MaterialRepository

        mat = Material(
            subject_id=subject_id,
            name=name,
            size_bytes=1024,
            mime="application/pdf",
            storage_path=f"/tmp/{name}.pdf",
            status=status or MaterialStatus.PROCESSED,
            uploaded_by_id=uploaded_by_id,
        )
        await MaterialRepository(self.s).add(mat)
        await self.s.commit()
        return mat

    async def tutor_conversation(self, owner_id, subject_id, *, title="Tutor Chat"):
        from db.models import Conversation, ConversationKind
        conv = Conversation(
            owner_id=owner_id, kind=ConversationKind.TUTOR,
            subject_id=subject_id, title=title,
        )
        self.s.add(conv)
        await self.s.commit()
        return conv

    async def doc_conversation(self, owner_id, *, title="Doc Chat"):
        from db.models import Conversation, ConversationKind
        conv = Conversation(
            owner_id=owner_id, kind=ConversationKind.DOC,
            subject_id=None, title=title,
        )
        self.s.add(conv)
        await self.s.commit()
        return conv

    async def message(self, conversation_id, role, text_="hello"):
        from db.models import Message, MessageRole
        role = role if isinstance(role, MessageRole) else MessageRole(role)
        msg = Message(conversation_id=conversation_id, role=role, text=text_)
        self.s.add(msg)
        await self.s.commit()
        return msg

    async def feedback(self, message_id, user_id, value):
        from db.models import Feedback, FeedbackValue
        value = value if isinstance(value, FeedbackValue) else FeedbackValue(value)
        fb = Feedback(message_id=message_id, user_id=user_id, feedback=value)
        self.s.add(fb)
        await self.s.commit()
        return fb


    async def doc_file(self, conversation_id, *, status=None, name="doc.pdf"):
        from db.models import DocumentFile, DocumentFileStatus
        from repositories.document_file_repository import DocumentFileRepository

        f = DocumentFile(
            conversation_id=conversation_id,
            name=name,
            size_bytes=1024,
            mime="application/pdf",
            storage_path=f"/tmp/{name}",
            status=status or DocumentFileStatus.READY,
        )
        await DocumentFileRepository(self.s).add(f)
        await self.s.commit()
        return f


@pytest_asyncio.fixture
async def seed(db) -> Seeder:
    return Seeder(db)


@pytest.fixture
def pdf_bytes() -> bytes:
    """A real, minimal, non-encrypted one-page PDF (generated via PyMuPDF)."""
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "DocMind test document. Hello world.")
    data = doc.tobytes()
    doc.close()
    return data
