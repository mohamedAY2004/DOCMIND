# Tests

Integration tests covering every **non-legacy** API endpoint (`/api/*` and
`/health`; the legacy `/api/v1/*` surface is intentionally excluded). They run
the real FastAPI app via `httpx.AsyncClient(ASGITransport)` against a real
Postgres + pgvector database, with **faked** LLM / embedding / vector-store
providers and the agent layer disabled. They double as a regression guard for
the bug-fix pass (H2, H4, M1, M2, M4, M5, N2, N3, M6, super-only writes).

## Prerequisites

A running Postgres + pgvector. The repo's docker compose works; the tests
default to `postgresql+asyncpg://admin:pass123@localhost:5433/docmind_test`
(override via the `TEST_DATABASE_URL` env var). The test database is created and
migrated (`alembic upgrade head`) automatically on first run.

```bash
# 1. Start Postgres+pgvector on host port 5433 (matches src/.env)
cd backend/docker && POSTGRES_PORT=5433 docker compose up -d postgres

# 2. Install test deps (into the project env)
cd ../src && pip install -r requirements-test.txt

# 3. Run
pytest -q
```

Override the DB target if needed:

```bash
TEST_DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/docmind_test" pytest -q
```

## Layout

- `conftest.py` — harness: ensures + migrates the test DB, truncates all tables
  before each test, builds the app with a test session-maker + fake providers,
  and exposes the `client`, `db`, `seed` (domain row factory) and `pdf_bytes`
  fixtures plus the `auth_header(user)` helper.
- `fakes.py` — `FakeLLM` (deterministic embeddings + canned generation) and
  in-memory `FakeVectorDB`.
- `test_health.py`, `test_auth.py`, `test_system_access.py`, `test_subjects.py`,
  `test_materials.py`, `test_chat_tutor.py`, `test_chat_doc.py`,
  `test_chat_feedback.py`, `test_admin_users.py`, `test_admin_misc.py` — one
  module per router area; happy path + auth/RBAC/ownership/error guards.
- `test_errors.py`, `test_file_service.py` — pre-existing pure-unit tests (no DB).

## Notes

- Each test is isolated: an autouse fixture `TRUNCATE`s every ORM table before
  it runs, so tests can run in any order.
- Validation errors surface as **400** (the app maps FastAPI's 422 into the
  `{code,message,details}` envelope), not 422.
- Background indexing jobs run and are awaited by httpx, so upload → status
  flip (`processed` / `failed`) is observable in-test.
