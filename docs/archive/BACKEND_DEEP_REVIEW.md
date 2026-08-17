# DocMind Backend — Deep Code Review

**Scope:** FastAPI backend at `backend/src` — routes, services, repositories, ORM models, schemas, helpers, RAG pipeline, auth/RBAC, config, Alembic migrations, tests. Legacy asyncpg surface (`routes/legacy_router.py`, `routes/data.py`, `routes/nlp.py`, `controllers/`) was intentionally excluded.

**Note on prior-review docs:** The prompt referenced `BACKEND_REVIEW.md` / `BACKEND_BUGFIXES.md` at the repo root. These files do **not** exist in the working tree (the `BACKEND_REVIEW.md` shown as untracked in the opening git snapshot is no longer present). The prior bug-fix pass is instead captured in commit `1a34ea4 "bug fixes"`, which I diffed for context. Findings below are therefore reported as **new** unless explicitly cross-referenced to that commit. A "Verification of prior fixes" section at the end confirms the soundness of the `1a34ea4` changes.

---

## Summary table

| ID | Severity | File | One-line |
|----|----------|------|----------|
| H-1 | High | `services/admin_users_service.py:130-158` | Changing a user's role leaves orphaned instructor/student roster rows (data integrity / privilege residue) |
| H-2 | High | `services/admin_users_service.py:208-224`, `set_status` | Password reset & re-enable do not revoke existing JWTs — old sessions stay valid |
| M-1 | Medium | `routes/materials_router.py:133-191` | `test_bot` route contains substantial business logic + defines schemas in the route file (layering violation) |
| M-2 | Medium | `routes/admin_router.py:154-173` | `feedback_rows` route calls a repository directly and builds response rows (layering violation) |
| M-3 | Medium | `routes/materials_router.py:73` vs service | `upload_material` route blocks admins (`require_role(INSTRUCTOR)`) while the service explicitly allows admin — inconsistent RBAC |
| M-4 | Medium | `services/feedback_service.py:30-43`, `repositories/feedback_repository.py:30-43` | `upsert`/`get_by_message` key feedback by message only, not `(message, user)` — fragile if conversation sharing is ever added |
| M-5 | Medium | `helpers/deps.py:194-204` | `require_admin` / `require_instructor_or_admin` / `require_student` are broken-by-design and dead (return a dep factory, never used) |
| L-1 | Low | `services/file_service.py:144,151` | `get_settings().__dict__.get("FILES_DIR")` reads a non-existent setting — dead branch; storage dir is never configurable |
| L-2 | Low | `repositories/system_flag_repository.py:17-24` | `get_or_create` hardcodes `enabled=True`, ignoring `STUDENT_ACCESS_DEFAULT_ENABLED` config |
| L-3 | Low | `helpers/config.py:75` | `JWT_SECRET` ships a usable default (`"change-me-in-production"`) — no fail-fast in non-dev |
| L-4 | Low | `repositories/message_repository.py:58-66,88-101` | `count_since` and `previous_user_message` are dead code (unused by non-legacy surface) |
| L-5 | Low | `services/document_chat_service.py:200-208`, `tutor_chat_service.py:143-151` | `update_conversation` sets `updated_at` only when a title is supplied; a no-op PATCH silently returns 200 with stale data |
| N-1 | Info | `db/models/conversation.py:33-35` + `subject_service.delete` | `subject_id ON DELETE SET NULL` is unreachable: delete is blocked whenever any conversation references the subject |
| N-2 | Info | `main.py:76,149` | Deprecated `@app.on_event("startup"/"shutdown")` — replace with lifespan handler |

---

## Detailed findings

### H-1 — Role change leaves orphaned roster rows (data integrity + stale access)
**File:** `services/admin_users_service.py:130-158` (`update`)

```python
if body.role is not None:
    user.role = UserRole(body.role)
await self._apply_enrollment(user, body.enrolledSubjectIds)
```

When an admin changes a user's `role`, nothing cleans up the role-specific association tables:

- Demoting an **instructor → student** leaves their rows in `subject_instructors` (including any `super` role). `get_super_instructor` / `is_instructor_of` will still return them, so material-management authorization in `MaterialService._ensure_can_upload` keeps treating a now-student as the subject's super instructor.
- Promoting a **student → instructor** leaves rows in `subject_students`, so `is_student_of` still passes and the per-subject student gate (`ensure_subject_access`, tutor enrollment) still grants the old enrollments.
- `_apply_enrollment` only runs for `role == STUDENT` and only when `enrolledSubjectIds` is provided, so it does not compensate.

**Impact:** Stale privilege residue and inconsistent rosters. A demoted instructor can retain `super` upload rights; a promoted instructor retains phantom student enrollments. Also affects the partial-unique `uq_subject_one_super` invariant if the demoted super is later re-added.

**Fix:** On any role transition, purge the now-irrelevant association rows in the same transaction — e.g. when leaving `INSTRUCTOR`, `DELETE FROM subject_instructors WHERE user_id = :id`; when leaving `STUDENT`, `DELETE FROM subject_students WHERE user_id = :id`. Add a repository method and call it from `update` whenever `body.role` differs from the current role.

---

### H-2 — Password reset and account re-enable do not revoke live tokens
**File:** `services/admin_users_service.py:160-224`

`reset_password` rotates `password_hash` but issues no token revocation. `get_current_user` (`helpers/deps.py:91-97`) only rejects a token when the user row is missing or `status == DISABLED`; it does **not** compare a token-issuance epoch against the password-changed time. Likewise, `set_status(... ENABLED)` after a disable does nothing to old tokens (those were never blocklisted on disable — disable relies purely on the live status check, which is fine, but a re-enable then resurrects nothing because tokens were never invalidated).

**Impact:** After an admin resets a (possibly compromised) account's password, any previously issued JWT for that user remains valid until its natural `exp` (default 12h, `JWT_EXPIRE_MINUTES=720`). The blocklist only ever receives a `jti` via explicit `/auth/logout`, so an attacker holding a stolen token is unaffected by the reset.

**Fix:** Add a per-user invalidation epoch (e.g. `users.tokens_valid_from` timestamp) bumped on password reset / forced logout, and reject tokens whose `iat` precedes it inside `get_current_user`. The JWT already carries `iat` (`helpers/auth.py:50`), so no token-format change is needed — only a new column + one comparison.

---

### M-1 — `test_bot` route holds business logic and defines schemas inline
**File:** `routes/materials_router.py:125-191`

```python
class _TestBotRequest(BaseModel): ...
class _TestBotResponse(BaseModel): ...

@router.post("/{subject_id}/test-bot", ...)
async def test_bot(...):
    subject = await SubjectRepository(session).get(subject_id)
    if subject is None: raise APIError(...)
    processed = await MaterialRepository(session).count_processed(subject_id)
    if processed == 0: raise APIError(...)
    ...
    answer = await rag.answer(collection, body.message, ...)
```

This route violates the project's thin-route rule on multiple counts: it instantiates two repositories directly, performs the subject-existence and "subject ready" checks, raises `APIError` from the route layer, builds the subject label, and orchestrates the RAG/agent call. It also defines `_TestBotRequest` / `_TestBotResponse` in the route file, contradicting "don't define schemas in route files."

**Impact:** Logic duplication (`TutorChatService._ensure_subject_ready` already does the same checks), and authorization is weaker than the rest of materials — note it only requires `INSTRUCTOR | ADMIN` but never checks the instructor is assigned to the subject, so **any** instructor can probe **any** subject's indexed corpus (a mild IDOR-style information exposure across subjects).

**Fix:** Move the whole handler into a `MaterialService.test_bot(caller, subject_id, message, rag, agent)` method that calls `_ensure_can_read` (which enforces instructor-on-roster) + a shared "subject ready" check; move the request/response models into `schemas/material.py` (or `schemas/chat.py`).

---

### M-2 — `feedback_rows` admin route queries the repo and shapes rows
**File:** `routes/admin_router.py:154-173`

```python
rows, total = await FeedbackRepository(session).list_rows(...)
items = [FeedbackRowResponse(**r) for r in rows]
return Page.build(items=items, total=total, params=params)
```

The route instantiates `FeedbackRepository` directly and assembles the paginated response — there is no service layer between the route and the repository for this endpoint, unlike every other admin endpoint (which goes through `AdminUsersService` / `AdminStatsService` / `AdminActivityService`).

**Impact:** Inconsistent layering; the filter/enum-coercion logic (`FeedbackValue(feedback)`) lives in the route. Harder to unit-test and to reuse.

**Fix:** Add `AdminStatsService.list_feedback_rows(params, semester, subject_id, feedback)` (or a dedicated `AdminFeedbackService`) and have the route call that single method.

---

### M-3 — `upload_material` route excludes admins, contradicting the service
**File:** `routes/materials_router.py:66-74` vs `services/material_service.py:101-127`

The upload route gates on `require_role(UserRole.INSTRUCTOR)` (admin excluded), but `MaterialService._ensure_can_upload` begins with `if user.role == UserRole.ADMIN: return`. The `PATCH` and `DELETE` material routes use `require_role(INSTRUCTOR, ADMIN)`.

**Impact:** An admin can patch/delete materials but cannot upload them — an inconsistent and surprising RBAC matrix. The service's admin branch for upload is unreachable through the API.

**Fix:** Decide the intended policy and make route + service agree. If admins may manage materials end-to-end, change the route to `require_role(UserRole.INSTRUCTOR, UserRole.ADMIN)`. If not, drop the admin branch from `_ensure_can_upload`.

---

### M-4 — Feedback is keyed per-message, not per-(message, user)
**Files:** `repositories/feedback_repository.py:24-51`, `db/models/feedback.py:26-28`, `services/feedback_service.py:72-84`

`Feedback.message_id` is `unique=True`, and `get_by_message` / `upsert` / `delete_by_message` all filter by `message_id` alone. `FeedbackService.delete` fetches the row by message, then checks `existing.user_id == caller.id`.

This is **correct today** only because conversations are single-owner and only the owner can reach `_assert_can_feedback`. But the model encodes "one feedback row per message globally," not "per user per message." If conversation sharing or instructor feedback is ever added, the unique constraint will cause one user's vote to overwrite or block another's, and `delete` will 403 the second user.

**Impact:** Latent correctness/IDOR hazard; the data model does not match the stated intent (`user_id` column exists yet is not part of the uniqueness key).

**Fix:** Either (a) document that feedback is intentionally one-per-message and drop the unused per-user semantics, or (b) make uniqueness `(message_id, user_id)` and key all three accessors on both columns. Given `user_id` already exists and `delete` checks ownership, option (b) is the more defensible direction.

---

### M-5 — Convenience role deps are broken and dead
**File:** `helpers/deps.py:194-204`

```python
def require_admin() -> Callable[[User], User]:
    return require_role(UserRole.ADMIN)
```

These return a dependency *factory result* (a function), so a route would have to write `Depends(require_admin())` — but `require_role` itself already returns the checker, so `Depends(require_admin())` works by luck while `Depends(require_admin)` would inject the wrong thing. In practice **no route uses them**; every route calls `require_role(...)` directly (confirmed by grep). CLAUDE.md advertises `require_admin`, `require_instructor_or_admin`, `require_student` as the canonical gating deps, so the docs and code diverge.

**Impact:** Dead, misleading API surface; a future caller following CLAUDE.md is likely to wire them incorrectly.

**Fix:** Either delete them, or convert them into actual usable dependencies (`require_admin = require_role(UserRole.ADMIN)` as a module-level value, used as `Depends(require_admin)`), and migrate routes to the documented names.

---

### L-1 — `FILES_DIR` lookup reads a setting that never exists
**File:** `services/file_service.py:143-154`

```python
base = Path(get_settings().__dict__.get("FILES_DIR") or _default_files_dir())
```

`FILES_DIR` is not a field on `Settings`, and `extra="ignore"` means even an env var named `FILES_DIR` is dropped before it reaches the instance `__dict__`. The `or _default_files_dir()` branch is therefore always taken. Reaching into `__dict__` also bypasses the mandated `get_settings()` accessor pattern.

**Impact:** Upload storage location is silently un-configurable; the code reads as if it supported override but does not.

**Fix:** Add a real `FILES_DIR: Optional[str] = None` field to `Settings` and read `get_settings().FILES_DIR or _default_files_dir()`.

---

### L-2 — Student-access flag default ignores configured value
**File:** `repositories/system_flag_repository.py:17-24`

`get_or_create` hardcodes `StudentAccessFlag(id=1, enabled=True, ...)`, ignoring `Settings.STUDENT_ACCESS_DEFAULT_ENABLED` (`helpers/config.py:90`). The config knob is effectively dead.

**Impact:** Deployments that set `STUDENT_ACCESS_DEFAULT_ENABLED=false` still come up with student access **on** until an admin toggles it.

**Fix:** Seed `enabled=get_settings().STUDENT_ACCESS_DEFAULT_ENABLED` (the repository can read settings, or the caller can pass the default in).

---

### L-3 — Usable default JWT secret
**File:** `helpers/config.py:75`

```python
JWT_SECRET: str = "change-me-in-production"
```

A static default means a misconfigured deployment signs and accepts tokens with a publicly known key. There is no startup assertion that the secret was overridden.

**Impact:** If `.env` is missing/incomplete in production, all JWTs are forgeable.

**Fix:** Make `JWT_SECRET` required (no default) so `Settings()` raises at boot if unset, or add a startup check that refuses to run with the placeholder value outside an explicit dev mode.

---

### L-4 — Dead repository methods
**File:** `repositories/message_repository.py:58-66` (`count_since`), `88-101` (`previous_user_message`)

Grep across the non-legacy surface shows no callers. `previous_user_message` is superseded by the correlated subquery in `FeedbackRepository.list_rows`.

**Fix:** Remove, or wire up if intended for analytics.

---

### L-5 — No-op conversation PATCH returns stale 200
**Files:** `services/document_chat_service.py:200-208`, `services/tutor_chat_service.py:143-151`

```python
if title is not None:
    conv.title = title
    conv.updated_at = datetime.now(timezone.utc)
count = await self._conversations.message_count(conv.id)
return _conv_response(conv, count)
```

A `PATCH` with `title=None` (the schema allows omission) performs no write but still returns 200 with the unchanged conversation. This is benign but inconsistent — the endpoint advertises an update that may do nothing without signalling it.

**Fix:** Either treat an empty patch as a 400, or document the no-op behavior. Low priority.

---

### N-1 — `conversations.subject_id ON DELETE SET NULL` is unreachable
**File:** `db/models/conversation.py:33-35`, `alembic/versions/0001_initial.py:249`, vs `services/subject_service.py:190-205`

The FK uses `SET NULL`, but `SubjectService.delete` raises `CONFLICT` whenever *any* conversation references the subject, so the cascade never fires in normal operation. Not a bug, but the schema and the business rule express contradictory intents. If the conflict guard is ever relaxed, tutor conversations would silently lose their `subject_id` and `_ensure_subject_ready("")` would then 404 them.

**Fix:** Align the two — either allow deletion and rely on `SET NULL` (with downstream handling of null-subject tutor chats), or keep the guard and note that `SET NULL` is purely defensive.

---

### N-2 — Deprecated FastAPI startup/shutdown hooks
**File:** `main.py:76,149`

`@app.on_event("startup")` / `("shutdown")` are deprecated in current FastAPI/Starlette in favor of a `lifespan` context manager. Functional today; worth migrating to avoid future breakage and to make the provider singletons testable without the ASGI-transport workaround the test harness currently needs (`conftest.py:122-137` manually injects `app.state` because startup never fires).

---

## Verification of prior fixes (commit `1a34ea4`)

I diffed `1a34ea4` and reviewed the resulting code. The fixes are sound:

- **`0003_failed_index_status`** adds `'failed'` to `material_status` and `document_file_status` via `ALTER TYPE ... ADD VALUE IF NOT EXISTS`. Correct, idempotent, and PG12+-safe (the new value is not consumed in the same transaction). `MaterialResponse.status` / `DocumentFileResponse.status` Literals were updated to include `"failed"` (`schemas/material.py:14`, `schemas/chat.py:34`), and the background jobs now flip rows to `FAILED` on exception (`material_service.py:329-341`, `document_chat_service.py:444-454`) so files no longer hang in `indexing`/`processing`. Confirmed sound. Note `UpdateMaterialRequest.status` intentionally still excludes `failed` (you can't manually set a row to failed), which is reasonable.
- **`0004_one_super_per_subject`** adds a partial unique index `uq_subject_one_super`, mirrored in the ORM `__table_args__` (`db/models/subject_instructor.py:22-29`). `get_super_instructor` still orders + limits defensively. Sound. (Caveat: H-1 can still violate the *intent* by leaving a demoted user with a `super` row, though the DB index itself stays satisfied.)
- **`get_logout_claims`** now derives `expires_at` from the token's real `exp` claim (`helpers/deps.py:206-237`), so blocklist rows expire exactly when the token would — the previous meaningless expiry is fixed. The startup `purge_expired` sweep (`main.py:94-108`) bounds table growth. Sound.
- **`get_current_user` last-active throttle** (`helpers/deps.py:99-108`) with `LAST_ACTIVE_THROTTLE_SECONDS` correctly normalizes naive timestamps to UTC before comparison and avoids a per-GET UPDATE. Sound.
- **`RequestIDMiddleware`** now validates client-supplied `X-Request-Id` against `[A-Za-z0-9._-]{1,64}` before echoing (`helpers/middleware.py:16,22-31`), closing header-injection/log-forging. Sound.
- **`BaseRepository.count`** wraps the statement in a subquery (`repositories/base.py:33-40`), giving correct counts across joins/DISTINCT. Sound.
- **Orphaned-file cleanup** on row-insert failure in `material_service.upload` and `document_chat_service._save_file` (best-effort unlink) is correct; the streaming size check unlinks after the handle closes (Windows-safe). Residual risk: a commit failure *after* the service returns still orphans the file on disk — acknowledged in the code comment; a periodic sweep is the right long-term fix.

No prior fix was found to be regressed or incorrect.

---

## Test coverage gaps

The suite is broader than CLAUDE.md implies (integration tests over a real Postgres+pgvector with faked LLM/vector providers; ~83 test functions across 11 files). `test_errors.py` and `test_file_service.py` are pure-unit. Gaps worth closing:

1. **Role-transition cleanup (H-1):** no test asserts that demoting an instructor or promoting a student purges `subject_instructors` / `subject_students`. Add once H-1 is fixed.
2. **Token invalidation on password reset (H-2):** no test that an old token is rejected after `reset_password`. Add once H-2 is addressed.
3. **`test-bot` cross-subject access (M-1):** no test that a non-assigned instructor is blocked from another subject's `test-bot`. Currently it would (incorrectly) pass.
4. **`upload_material` admin behavior (M-3):** no test pins whether admins can/can't upload; behavior is currently inconsistent and untested.
5. **Background-indexing failure path:** `index_material_job` / `index_doc_file_job` flipping a row to `FAILED` on a parse/index exception is not exercised (the fake providers don't simulate failure). Add a fault-injection test so the `failed` enum path stays covered.
6. **`require_subject_access` 404-vs-403 ordering:** worth a test that a non-existent subject returns 404 while an existing-but-unenrolled subject returns 403 (the `ensure_subject_access` contract).
7. **Logout/blocklist expiry:** a test that a logged-out token's `jti` is rejected, and that `purge_expired` drops only past-due rows, would lock in the `get_logout_claims` fix.
8. **CORS / `X-Request-Id` middleware:** no test asserts the request-id validation regex rejects an injected value and mints a fresh one.
