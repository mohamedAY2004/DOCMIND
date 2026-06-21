# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

DocMind is a monorepo for an AI-powered document/RAG assistant for university education. Three surfaces share one backend API:

| Surface | Path | Stack |
|---------|------|-------|
| Backend API | `backend/src/` | Python 3.10+, FastAPI, SQLAlchemy 2 (async) + asyncpg, PostgreSQL + pgvector, Alembic |
| Web frontend | `frontend/src/` | React 19, Vite 7, Tailwind CSS 3, React Router 7, Axios |
| Mobile app | `mobile/docmind_app/lib/` | Flutter/Dart, GetX, Dio |

`portal-demo/` is a standalone static-HTML SSO login demo and is not wired into the apps.

## Commands

### Backend (`backend/src/`)

> **Environment:** the backend runs in the `mini-rag` conda env (Python 3.10) —
> `C:\Users\mohamed\miniconda3\envs\mini-rag\python.exe`. Activate it
> (`conda activate mini-rag`) before installing deps or running the API/tests;
> the conda `base` env is Python 3.13 and is **not** set up for this project.

```bash
# Start Postgres+pgvector (DB only) and run migrations + seed
cd backend/docker && docker compose up -d postgres && docker compose run --rm migrate

# Run the API
cd backend/src && pip install -r requirements.txt && uvicorn main:app --reload --host 0.0.0.0 --port 8000
# Docs at http://localhost:8000/docs

# Migrations (run from backend/src)
alembic revision --autogenerate -m "add <name>"
alembic upgrade head

# Tests (deps are NOT in requirements.txt — install them explicitly)
cd backend/src && pip install pytest==8.* pytest-asyncio==0.23.* httpx==0.27.*
pytest -q
pytest tests/test_file_service.py::test_name   # single test
```
Tests are intentionally thin right now (`tests/test_errors.py`, `tests/test_file_service.py`); DB-dependent tests are a planned follow-up.

### Frontend (`frontend/`)
```bash
npm install
npm run dev       # Vite dev server at http://localhost:5173
npm run build
npm run lint      # ESLint
npm run preview
```
Set `VITE_API_BASE_URL=http://localhost:8000` in `frontend/.env`.

### Mobile (`mobile/docmind_app/`)
```bash
flutter pub get
flutter run
flutter test
```

## Backend architecture (the important part)

**Strict layering — never skip a layer:**
```
Route (thin) → Service (business logic) → Repository (SQLAlchemy) → ORM Model
```
- Routes inject deps, call **one** service method, return a response model — no business logic, no queries.
- Services own all rules, instantiate repositories internally, and raise `APIError(ErrorCode.X, status_code=4xx)` from `helpers/errors.py` — **never** bare `HTTPException` inside services.
- Repositories hold SQLAlchemy queries only. Use the `BaseRepository[TModel]` generic for CRUD; extend for domain queries.
- Config always via `from helpers.config import get_settings` (cached singleton) — **never** read `os.environ` directly.
- Schema changes go through Alembic only — never mutate tables in application code.

**Dual-DB architecture — keep these paths separate:**
1. Official API (`/api/*`) — SQLAlchemy `AsyncSession` via `Depends(get_session)` (from `app.state.session_maker`). The session dependency commits/rolls back automatically; do **not** `await session.commit()` in services unless you need a mid-transaction flush.
2. Legacy/debug API (`/api/v1/data/*`, `/api/v1/nlp/*`) — raw asyncpg pool on `app.db_pool`, used **only** by `controllers/`. Do not add new code in `controllers/`.

**Provider abstraction (factory pattern):** LLM, embedding, and vector-store backends live under `stores/llm/`, `stores/vectordb/`, `stores/agent/` and are swapped purely via env vars (`GENERATION_BACKEND`, `EMBEDDING_BACKEND`, `VECTOR_DB_BACKEND`, `AGENT_ENABLED`) — no code changes needed to switch providers. Use enums (e.g. `stores/llm/LLMEnums.py`) instead of magic strings.

**Auth/RBAC:** Three roles — `student`, `instructor`, `admin`. Gate routes with deps `get_current_user`, `require_admin`, `require_instructor_or_admin`, `require_student`, `require_student_access`, and `ensure_subject_access` / `require_subject_access` for per-subject enrollment. JWT payload: `sub`, `role`, `jti`, `exp`; logout revokes `jti` via a blocklist checked in `get_current_user`. A global `StudentAccessFlag` can disable all student logins (returns `403 STUDENT_ACCESS_DISABLED`).

**Adding a backend feature:** ORM model in `db/models/<name>.py` (register in `db/models/__init__.py`) → Alembic migration → repository → service → Pydantic schemas in `schemas/<name>.py` (response schemas inherit `ORMModel`, requests inherit `BaseModel`; don't define schemas in route files) → router `routes/<name>_router.py` mounted in `main.py`.

Naming: `<domain>_router.py`, `<domain>_service.py`, `<domain>_repository.py`; ORM `PascalCase` class with `snake_case` `__tablename__`.

## Frontend architecture

- **Tailwind only.** No inline `style={{}}`, no CSS modules/styled-components; `index.css` is limited to the three `@tailwind` directives.
- Structure: `pages/` (one per route), `features/`, `routes/` (definitions + guards), `services/` (Axios API calls, no UI — `apiClient.js` holds the base instance + interceptors), `hooks/`, `components/ui/` + `components/layout/`.
- Small, single-responsibility components; prefer composition (`children`/slots) over large prop lists.
- Entry flow: `src/main.jsx` → `App.jsx` → `routes/index.jsx`.

## Mobile architecture

Clean Architecture per feature under `lib/features/<feature>/` with `data/` (datasources, dtos, repositories), `domain/` (entities, abstract repositories, usecases, failures), `presentation/` (pages, widgets, GetX controllers). Dependency direction: `presentation` → `domain` ← `data`.
- State/DI via GetX (`Get.put`/`Get.lazyPut`, `Obx`). Controllers call **use cases**, not repositories directly.
- All HTTP through `lib/core/network/dio_client.dart`; URLs/endpoints in `lib/core/api_constants.dart` (never hardcode); auth token attached via Dio interceptor.
- Named routes in `lib/core/routes/app_routes.dart`; navigate with `Get.toNamed(...)`. Repositories return `Either<Failure, T>`.
- Truly-shared code only in `lib/core/`.

## RAG pipeline

Ingestion: parse PDF/PPTX (PyMuPDF, python-pptx, pypdf) → chunk → embed → vector store. Query: (optional JSON-Planner agent decides whether to retrieve) → embed question → similarity search → (optional cross-encoder rerank) → build prompt with context → LLM response. Entry services: `ingestion_service.py`, `rag_service.py`, `document_chat_service.py`, `tutor_chat_service.py`.

**Optional reranking** (`stores/rerank/`, same factory pattern, `RERANK_*` env vars, OFF by default): when `RERANK_ENABLED=true`, `RAGService.search` over-fetches `limit * RERANK_OVERFETCH` candidates and a cross-encoder truncates back to `limit`. The `LOCAL_CROSS_ENCODER` backend needs the optional dep `pip install sentence-transformers` (kept out of `requirements.txt` to keep the image lean); it lazy-imports so the off-path never loads torch. Reranker faults soft-degrade to vector order — they never error a chat turn.
