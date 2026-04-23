# API → code map

Every endpoint required by `API_SPECIFICATION (1).md` is wired to an
`APIRouter` file, which delegates to a service, which delegates to one or more
repositories. Use this table when reviewing changes — if a row is missing, the
route is undocumented.

| Spec § | Method + Path | Router file | Service | Repository |
| --- | --- | --- | --- | --- |
| §3.5 | `GET /health` | `routes/health.py` | – | – |
| §4.1 | `POST /auth/login` | `routes/auth_router.py` | `AuthService` | `UserRepository`, `SystemFlagRepository`, `TokenBlocklistRepository` |
| §4.2 | `POST /auth/logout` | `routes/auth_router.py` | `AuthService` | `TokenBlocklistRepository` |
| §4.3 (rec.) | `GET /auth/me` | `routes/auth_router.py` | `AuthService` | `UserRepository` |
| §5.1 | `GET /system/student-access` | `routes/system_access_router.py` | `SystemAccessService` | `SystemFlagRepository` |
| §5.2 | `PATCH /admin/system/student-access` | `routes/system_access_router.py` | `SystemAccessService` | `SystemFlagRepository`, `ActivityRepository` |
| §6.1 | `GET /subjects/student` | `routes/subjects_router.py` | `SubjectService` | `SubjectRepository`, `MaterialRepository` |
| §6.2 | `GET /subjects/instructor` | `routes/subjects_router.py` | `SubjectService` | `SubjectRepository` |
| §6.3 | `GET /subjects/:id` | `routes/subjects_router.py` | `SubjectService` | `SubjectRepository`, `MaterialRepository` |
| §6.4 | `GET /subjects/:id/instructors` | `routes/subjects_router.py` | `SubjectService` | `SubjectRepository` |
| §6.6 | `GET /semesters` | `routes/subjects_router.py` | (inline) | `SemesterRepository` |
| §6.7 | `POST/PATCH/DELETE /admin/subjects[/:id]` | `routes/subjects_router.py` | `SubjectService` | `SubjectRepository`, `UserRepository`, `ActivityRepository` |
| §7.1 | `GET /subjects/:id/materials` | `routes/materials_router.py` | `MaterialService` | `MaterialRepository`, `UserRepository`, `SubjectRepository` |
| §7.2 | `POST /subjects/:id/materials` | `routes/materials_router.py` | `MaterialService` + `index_material_job` | `MaterialRepository`, `ActivityRepository` |
| §7.3 | `PATCH /subjects/:id/materials/:mid` | `routes/materials_router.py` | `MaterialService` | `MaterialRepository` |
| §7.4 | `DELETE /subjects/:id/materials/:mid` | `routes/materials_router.py` | `MaterialService` | `MaterialRepository`, `ActivityRepository` |
| §8.1.x | `POST/GET/DELETE /chat/tutor/conversations[/:id[/messages]]` | `routes/chat_tutor_router.py` | `TutorChatService` | `ConversationRepository`, `MessageRepository`, `SubjectRepository`, `MaterialRepository` |
| §8.1 compat | `POST /chat/tutor/:subjectId` | `routes/chat_tutor_router.py` | `TutorChatService` | same as above |
| §8.2.x | `POST/GET/DELETE /chat/doc/conversations[/:id[/files|messages]]` | `routes/chat_doc_router.py` | `DocumentChatService` + `index_doc_file_job` | `ConversationRepository`, `DocumentFileRepository`, `MessageRepository` |
| §8.2.5 | `POST /chat/doc` | `routes/chat_doc_router.py` | `DocumentChatService` | same as above |
| §8.4 | `POST/DELETE /chat/messages/:id/feedback` | `routes/chat_feedback_router.py` | `FeedbackService` | `FeedbackRepository`, `MessageRepository`, `ConversationRepository`, `ActivityRepository` |
| §10.1 | `GET/POST/PATCH/DELETE /admin/users[/…]` | `routes/admin_router.py` | `AdminUsersService` | `UserRepository`, `ActivityRepository` |
| §10.3 | `GET /admin/subjects/stats` | `routes/admin_router.py` | `AdminStatsService` | `SubjectRepository`, plus raw ORM joins |
| §10.4 | `GET /admin/feedback` | `routes/admin_router.py` | – | `FeedbackRepository.list_rows` |
| §10.5 | `GET /admin/activity` | `routes/admin_router.py` | `AdminActivityService` | `ActivityRepository` |
| §10.6 | `GET /admin/analytics/daily` | `routes/admin_router.py` | `AdminStatsService` | `MessageRepository.daily_rollup` |
| internal | `/api/v1/data/*` and `/api/v1/nlp/*` | `routes/legacy_router.py` | (controllers/) | asyncpg (unchanged) |

## Layer rules (enforced at review time)

- `routes/*` import only `schemas/`, `services/`, `helpers/deps`, `helpers/pagination` and FastAPI types.
- `services/*` import `repositories/`, `schemas/`, `helpers/errors`, `helpers/auth`, `helpers/config`, `services/*`, and vector/LLM clients via parameters.
- `repositories/*` import only `db/`, `schemas/common`, SQLAlchemy.
- Nothing outside `db/models/*` imports SQLAlchemy model classes.
- Every mutation visible to admins emits exactly one `ActivityLogger.record(...)` call from the service (never the route).

## Tests (to be added)

Pytest + `httpx.AsyncClient` suites live at `src/tests/`:

- `test_auth.py` — login happy path, wrong credentials, student-gate 403, logout revokes JTI.
- `test_subjects.py` — role-scoped listing + instructor self-only guard.
- `test_materials.py` — upload → status transitions → delete.
- `test_chat_doc.py` — create conversation with files, send message, feedback.
- `test_admin_matrix.py` — RBAC matrix for every admin endpoint (§15).

See `docs/TESTING.md` (TBD) for fixtures and the in-memory pgvector harness.
