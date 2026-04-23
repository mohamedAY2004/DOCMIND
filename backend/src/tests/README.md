# Tests

Tests are intentionally thin at this stage — the first implementation PR ships
the domain + route surface; a follow-up PR will populate the full matrix.

## How to run (once populated)

```bash
cd src
pip install -r requirements.txt pytest==8.* pytest-asyncio==0.23.* httpx==0.27.*
pytest -q
```

## Structure (target)

- `conftest.py` — fixtures for the async app, a throw-away test database,
  and a fake LLM/embedding/vectordb trio.
- `test_auth.py` — login happy path, wrong credentials, student-gate 403,
  logout → token revoked → subsequent call is 401.
- `test_subjects.py` — role-scoped listing + instructor self-only guard,
  admin CRUD.
- `test_materials.py` — upload → status transitions → delete + 415/413
  error cases.
- `test_chat_doc.py` — create conversation with files, send message,
  feedback upsert + delete.
- `test_chat_tutor.py` — SUBJECT_NOT_READY, happy path.
- `test_admin_matrix.py` — spec §15 RBAC matrix, one test per endpoint ×
  each role.
- `test_errors.py` — validates the `{code,message,details}` envelope on
  every non-success path.

## Why isn't this populated now?

Because the DB-dependent tests require a pgvector-enabled Postgres (or a
dockerized testcontainers fixture) and a fake embedding backend. That is a
separate PR — see the follow-up issue tracker.
