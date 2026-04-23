# DocMind — Backend API Specification

> Source of truth for the REST API that the DocMind frontend (React 19 + Vite) consumes.
> This document is intentionally exhaustive. Every constraint, enum, status code, error
> code, validation rule, and side effect the frontend already depends on is listed here.
> If something is not listed, ask before making an assumption.

- **Document version:** 1.0
- **Frontend repo:** `docmind-frontend`
- **Target base URL (dev):** `http://localhost:8000/api`
- **Target base URL (prod):** whatever `VITE_API_BASE_URL` points to (the frontend defaults to `/api` when the variable is unset)
- **Transport:** HTTPS in staging / prod; HTTP allowed only on localhost
- **Content type:** `application/json; charset=utf-8` for every endpoint except multipart file uploads (`multipart/form-data`)
- **Character encoding:** UTF-8 everywhere
- **Timezone:** all timestamps MUST be ISO-8601 UTC (`YYYY-MM-DDTHH:mm:ss.sssZ`). The frontend formats to local time in the UI.
- **Language / locale:** API responses must not contain localized strings. Copy shown to end users is rendered client-side.

---

## 1. Glossary

| Term | Meaning |
|---|---|
| **User** | Any account that can log in. Role is one of `student`, `instructor`, `admin`. |
| **Subject** | A course (slug id, e.g. `data-structures`). Has 0…N instructors and a shared list of materials. |
| **Instructor** | A `user` with role `instructor`. A single instructor can co-teach multiple subjects; a single subject can be co-taught by multiple instructors. |
| **Material** | A file (PDF or PPTX) uploaded against a subject. Shared across every instructor assigned to that subject. |
| **Document chat** | A student-only chat session where the AI reasons over files the student just uploaded (PDF / PPTX / PNG). |
| **Tutor chat** | A student-only chat session bound to a Subject; the AI uses the subject's Materials as knowledge base. |
| **Feedback** | Per AI message thumbs up / thumbs down signal used for reporting. |
| **Semester** | Label used in analytics filters (e.g. `fall-2025`). |
| **Student access** | A global on/off toggle controlled by admins; when off, students cannot log in and any authenticated student hitting the API gets `403` with `code=STUDENT_ACCESS_DISABLED`. |

---

## 2. Authentication & Authorization

### 2.1 Transport

- Authentication uses **Bearer JWT**. The frontend stores the token in `localStorage` under the key `auth_token` and sends it on every request as:
  ```
  Authorization: Bearer <token>
  ```
- The frontend automatically removes the token and navigates to `/login` on any `401` response. The backend MUST return `401` (not `403`) when the token is missing, invalid, malformed, or expired.
- Tokens MUST include at minimum: `sub` (user id), `role`, `iat`, `exp`. Suggested expiry: 12 hours for web sessions.
- Tokens should be signed with `HS256` or `RS256`. The backend is the single source of truth; the frontend never inspects the token payload.
- Password hashing MUST use `bcrypt` (cost ≥ 12), `argon2id`, or equivalent. Plaintext storage is forbidden.

### 2.2 Roles

Exactly three roles are supported. There is no `guest`, no `public_student`, no `anonymous` — the frontend has been purged of any such flow.

| Role | Allowed frontend routes |
|---|---|
| `student` | `/home`, `/chat`, `/tutors`, `/tutors/chat`, `/student-unavailable` |
| `instructor` | `/instructor`, `/instructor/subject/:subjectId` |
| `admin` | `/admin`, `/admin/users`, `/admin/subjects`, `/admin/analytics`, `/admin/system-access` |

Role enforcement on the API MUST mirror the routing table: a student token calling `/admin/*` MUST receive `403`.

### 2.3 Student-access gate (critical)

There is a single global flag `studentAccess.enabled` managed from the admin panel (see §9). It has these effects:

1. **Login.** When `enabled === false`, a login attempt for a `student` user MUST return `403` with body:
   ```json
   { "code": "STUDENT_ACCESS_DISABLED", "message": "optional admin-provided message" }
   ```
   and MUST NOT issue a token. Instructors and admins log in normally.
2. **Authenticated student calls.** Every student-scoped endpoint (see the `student` role rows in §4 onward) MUST also return the same `403 STUDENT_ACCESS_DISABLED` body when `enabled === false`. The frontend's axios response interceptor watches for this and redirects to `/student-unavailable`.
3. **Polling.** The frontend polls `GET /system/student-access` every 60 seconds and on window focus. The endpoint MUST remain public (no auth required) so that the login page can render a banner.

### 2.4 Error model

All errors MUST return JSON with this shape (the frontend reads `message` for toasts and `code` for special handling):

```json
{
  "code": "MACHINE_READABLE_CODE",
  "message": "Human readable sentence.",
  "details": { "field": "optional per-field validation errors" }
}
```

Required `code` values used by the frontend today:

| HTTP | `code` | When |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Request body failed validation; populate `details`. |
| 401 | `UNAUTHENTICATED` | Missing / expired / bad token. Frontend clears storage and redirects to `/login`. |
| 403 | `STUDENT_ACCESS_DISABLED` | Global student access is off. Frontend redirects to `/student-unavailable`. |
| 403 | `FORBIDDEN` | Role mismatch / not allowed on this resource. |
| 404 | `NOT_FOUND` | Resource does not exist. |
| 409 | `CONFLICT` | Duplicate resource (e.g. uploading a material with a name that already exists in the subject). |
| 413 | `FILE_TOO_LARGE` | Upload exceeded size limit. |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | File type not allowed. |
| 422 | `UNPROCESSABLE` | Well-formed but semantically invalid (e.g. toggling a user's own status). |
| 429 | `RATE_LIMITED` | Rate limit; include `Retry-After` header. |
| 500 | `INTERNAL_ERROR` | Unhandled server error. |

Every response (success or error) MUST include a `X-Request-Id` header with a UUID so support can correlate logs.

### 2.5 CORS

The API MUST allow the frontend origin (dev: `http://localhost:5173`, prod: as configured).
Allowed headers: `Authorization, Content-Type, X-Request-Id`.
Allowed methods: `GET, POST, PATCH, PUT, DELETE, OPTIONS`.
Credentials are NOT required (tokens are sent explicitly), but setting `Access-Control-Allow-Credentials: true` is acceptable.

### 2.6 Rate limiting

Recommended defaults (not currently enforced by the frontend, but the frontend handles `429` gracefully via toasts):

| Endpoint group | Limit |
|---|---|
| `POST /auth/login` | 10 / min / IP |
| `POST /chat/**` | 60 / min / user |
| `POST /uploads/**` | 20 / hour / user |
| All others | 120 / min / user |

---

## 3. Common conventions

### 3.1 Versioning

All endpoints in this document live under the un-versioned base URL (e.g. `/auth/login`). If a breaking change is required, add `/v2/…` paths and keep `/v1` responding for at least one release cycle.

### 3.2 Pagination

List endpoints that can grow unbounded MUST support these query params:

| Param | Type | Default | Notes |
|---|---|---|---|
| `page` | int ≥ 1 | `1` | 1-indexed. |
| `pageSize` | int, 1..100 | `20` | |
| `sort` | string | — | e.g. `name:asc`, `registeredAt:desc`. Whitelist per endpoint. |
| `search` | string | — | Free-text search; per endpoint you must document which fields are searched. |

Response envelope for paginated lists:

```json
{
  "items": [ /* array of resource objects */ ],
  "page": 1,
  "pageSize": 20,
  "total": 137,
  "totalPages": 7
}
```

Endpoints that are known to be small (e.g. `GET /subjects`, `GET /semesters`) MAY return a bare array.

### 3.3 IDs

- **User id:** opaque server-generated string. The frontend's current mock uses `U001`-style ids; the real backend MAY use UUIDs or numeric ids. The frontend treats them as opaque strings and compares with `===`.
- **Subject id:** human-readable slug (lowercase, hyphenated). The backend MUST expose it as `id`, e.g. `data-structures`. Slugs MUST be unique and URL-safe (`[a-z0-9-]+`, length 2..64).
- **Material id:** opaque server-generated string.
- **Conversation id / Message id:** opaque server-generated strings.
- **Feedback id:** opaque server-generated string.

The frontend NEVER mints server-side ids. Any `id` it sends is an echo of a value the server previously returned.

### 3.4 Datetime / relative time

- Absolute timestamps in request / response bodies: ISO-8601 UTC strings (`2026-03-15T14:23:00.000Z`).
- `lastActive`, `registeredAt` etc. on users: same ISO-8601. The frontend is free to format (currently renders `YYYY-MM-DD`).
- Human-relative strings like `"2 min ago"` that appear in activity logs MAY either be:
  (a) computed client-side from an ISO `createdAt` — **preferred**, or
  (b) returned as a pre-computed string in a `time` field.
  Whichever you pick, stay consistent across all activity responses.

### 3.5 Health check

The frontend does not consume it but ops needs it:

```
GET /health    →  200  { "status": "ok", "uptimeSec": 12345, "version": "1.0.0" }
```

---

## 4. Auth endpoints

### 4.1 `POST /auth/login`

Used by `src/services/authService.js → login()`.

**Authentication:** none.

**Request body:**

```json
{
  "username": "string, 1..64 chars, trimmed, case-sensitive",
  "password": "string, 1..128 chars"
}
```

Validation constraints:

- Both fields required; missing or empty ⇒ `400 VALIDATION_ERROR`.
- Username is compared **exactly** as stored. The current mock uses `user`, `instructor`, `instructor2`, `1`. Backend may migrate to email-based usernames, but the login contract does not care — the frontend just sends whatever the user typed.
- On failure (wrong credentials, unknown user, disabled account): return `401 UNAUTHENTICATED` with a **generic** message (do not leak whether the user exists). Frontend displays it verbatim.

**Success response** `200 OK`:

```json
{
  "token": "<JWT>",
  "user": {
    "id": "U003",
    "username": "instructor",
    "name": "Dr. Nour Farid",
    "role": "instructor"
  },
  "redirect": "/instructor",
  "welcomeMessage": "Welcome back, Dr. Nour Farid!"   // optional
}
```

Field rules:

- `token` — JWT string. Required.
- `user.id` — server id. Required, non-empty.
- `user.username` — echo of the typed username. Required.
- `user.name` — display name used in UI toasts and headers. Required, non-empty.
- `user.role` — one of `student | instructor | admin`. Required.
- `redirect` — absolute frontend path to send the user after login. Required. MUST match the role:
  - `student` ⇒ `/home`
  - `instructor` ⇒ `/instructor`
  - `admin` ⇒ `/admin`
- `welcomeMessage` — optional override for the toast. If omitted the frontend uses `Welcome back, <username>!`.

**Student-access-disabled response** `403 Forbidden`:

```json
{
  "code": "STUDENT_ACCESS_DISABLED",
  "message": "The platform is closed until 3:00 PM for exams."
}
```

MUST only be used when the credentials are valid AND the user's role is `student` AND the global student-access flag is `false`. Instructor / admin logins are never blocked by this flag.

**Other errors:** `401 UNAUTHENTICATED` for bad credentials, `429 RATE_LIMITED` for brute-force protection.

### 4.2 `POST /auth/logout`

Used by `src/services/authService.js → logout()`.

**Authentication:** Bearer token.

**Request body:** empty.

**Response:** `204 No Content`.

Server MUST revoke the token (add to a denylist, or rely on short-lived JWT with refresh-token invalidation). Even if the server-side revoke fails, the frontend will still clear local storage; so the endpoint SHOULD be idempotent.

### 4.3 `GET /auth/me` *(recommended, not yet consumed)*

Returns the current user. Recommended for future use (e.g. rehydrating auth state after F5).

```
GET /auth/me
→ 200 { "user": { "id", "username", "name", "role" } }
→ 401 UNAUTHENTICATED
```

---

## 5. System access endpoints

Consumed by `src/services/systemAccessService.js`, the admin `SystemAccess` page, the login page (banner), and `StudentAccessGate`.

### 5.1 `GET /system/student-access`

Public, no auth. Also safe to call while authenticated.

```
GET /system/student-access
```

**Response** `200 OK`:

```json
{
  "enabled": true,
  "message": "",
  "updatedAt": "2026-03-10T12:00:00.000Z"
}
```

- `enabled` — boolean, required.
- `message` — string, MAY be empty. Max 500 chars. Plain text; newlines allowed. Will be rendered as-is (no HTML).
- `updatedAt` — ISO-8601 or `null` if never modified.

### 5.2 `PATCH /admin/system/student-access`

Admin only (role=`admin`). Used by the SystemAccess page.

**Request body:**

```json
{
  "enabled": false,
  "message": "The platform is closed until 3:00 PM for exams."
}
```

Validation:

- `enabled` — required boolean.
- `message` — optional string. If omitted, server MUST keep the existing message. If empty string is explicitly sent, clear the message.
- Max length 500 chars; reject with `400 VALIDATION_ERROR`.

**Response:** same shape as `GET /system/student-access`, with `updatedAt` bumped to `now()`.

**Side effects:**

- Toggling `enabled` to `false` MUST immediately start failing student-scoped endpoints with `403 STUDENT_ACCESS_DISABLED` (no grace period).
- MUST write an entry to the admin activity log (see §10.5).

---

## 6. Subjects

Subject data is read by students (`ChatWithTutors`), instructors (`InstructorHome`, `InstructorSubject`), and admins (subject stats, analytics).

### 6.1 Resource shape

```json
{
  "id": "data-structures",
  "title": "Data Structures",
  "description": "Master the fundamentals of organizing, managing, and storing data.",
  "courseCode": "CS-123 • Semester A",
  "pdfCount": "12 PDFs",
  "instructorIds": ["U003", "U005"]
}
```

Field rules:

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string slug | yes | `[a-z0-9-]{2,64}`; unique. |
| `title` | string | yes | 1..120 chars. |
| `description` | string | yes | 1..500 chars. Plain text. |
| `courseCode` | string | yes | Free-form display label, e.g. `"CS-123 • Semester A"`. Max 80 chars. |
| `pdfCount` | string | yes | Pre-formatted label for the card (e.g. `"12 PDFs"`). Server MAY compute this from materials. **Must always be a string** — the UI prints it verbatim. |
| `instructorIds` | string[] | yes | 0..N ids; every id MUST resolve to a `user` with role `instructor`. An empty array means "no instructors assigned yet". |

### 6.2 `GET /subjects/student`

**Role:** `student`. Returns the list of subjects the student can see (currently all subjects; the backend MAY filter by enrollment if that is modeled server-side).

```
GET /subjects/student
→ 200  Subject[]   // bare array is OK; small list
```

### 6.3 `GET /subjects/instructor?instructorId=U003`

**Role:** `instructor`. If `instructorId` is omitted, the server MUST default to the caller's id (an instructor can only query their own subjects; requesting someone else's id returns `403 FORBIDDEN`).

```
GET /subjects/instructor
GET /subjects/instructor?instructorId=U003
→ 200  Subject[]
```

Returns every subject where `instructorIds` includes the requested id.

### 6.4 `GET /subjects/:subjectId`

**Role:** any authenticated user. Returns a single subject.

```
GET /subjects/data-structures
→ 200  Subject
→ 404  NOT_FOUND
```

### 6.5 `GET /subjects/:subjectId/instructors`

**Role:** any authenticated user. Returns the full instructor profiles for the subject's roster (convenience; saves the frontend a join).

**Response element shape:**

```json
{
  "id": "U003",
  "name": "Dr. Nour Farid",
  "email": "nour@docmind.edu"
}
```

```
GET /subjects/data-structures/instructors
→ 200  Instructor[]
→ 404  NOT_FOUND
```

### 6.6 `GET /semesters`

**Role:** any authenticated user (admin uses it today; other roles may not). Returns the list of semesters used by the analytics / subject-management filters.

```
GET /semesters
→ 200 [ { "id": "fall-2025", "label": "Fall 2025" }, … ]
```

Ordering: whatever makes sense (most-recent first is a good default). At least the current list below MUST be returned to preserve current UX:

- `fall-2024` → `"Fall 2024"`
- `spring-2025` → `"Spring 2025"`
- `fall-2025` → `"Fall 2025"`
- `spring-2026` → `"Spring 2026"`

New semesters MAY be added by admins; a write endpoint is out of scope for v1 (manage via DB / seed).

### 6.7 Admin-only subject endpoints *(recommended for v1)*

The admin panel currently only READS subjects; it does not create them. Writes are deferred to v1.1. If implemented, follow this contract:

```
POST   /admin/subjects           body: { title, description, courseCode, instructorIds }
PATCH  /admin/subjects/:id       body: partial Subject
DELETE /admin/subjects/:id
```

Role: `admin`. Validation identical to §6.1. Deleting a subject MUST cascade-delete its materials and disallow if it has active conversations (return `409 CONFLICT`).

---

## 7. Subject materials (instructor uploads)

Materials are PDFs / PPTX files attached to a subject. They are **shared across every instructor** assigned to the subject, and they are what powers the tutor-chat AI.

### 7.1 Resource shape

```json
{
  "id": "M-DS-1",
  "name": "Lecture_01_Introduction_to_Trees.pdf",
  "size": "2.4 MB",
  "date": "Jan 15, 2025",
  "status": "processed",
  "uploadedById": "U003",
  "uploadedByName": "Dr. Nour Farid",
  "uploadedByInitials": "NF"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Opaque. |
| `name` | string | yes | Original filename including extension. 1..255 chars. |
| `size` | string | yes | Human-formatted size, e.g. `"2.4 MB"` / `"780 KB"`. The frontend does **not** re-format this; always return a pretty string. Server MAY also include a `sizeBytes` integer for future use. |
| `date` | string | yes | Human-formatted upload date, e.g. `"Jan 15, 2025"`. Again, pre-formatted server-side. MAY additionally include `createdAt` (ISO-8601). |
| `status` | enum | yes | `"indexing"` or `"processed"`. No other values are rendered. |
| `uploadedById` | string | yes | Id of the instructor who uploaded it. MUST be one of the subject's `instructorIds` (or historical — see §7.5). |
| `uploadedByName` | string | yes | Display name. Server MAY compute from `uploadedById`. |
| `uploadedByInitials` | string | no | 1..3 uppercase letters. If omitted, frontend derives from `uploadedByName`. |

### 7.2 File constraints (enforced by server; frontend only hints)

- Allowed MIME types / extensions:
  - `application/pdf` (`.pdf`)
  - `application/vnd.openxmlformats-officedocument.presentationml.presentation` (`.pptx`)
- Max size: **50 MiB** per file. Reject with `413 FILE_TOO_LARGE`.
- Max filename length: 255 characters.
- Reject files that:
  - are empty (`422 UNPROCESSABLE`),
  - fail a virus scan (`422 UNPROCESSABLE` with `code: "FILE_UNSAFE"`),
  - are password-protected PDFs (`422 UNPROCESSABLE` with `code: "FILE_ENCRYPTED"`).

### 7.3 `GET /subjects/:subjectId/materials`

**Role:** `instructor` (must be on the subject's roster) or `admin`.

```
GET /subjects/data-structures/materials
→ 200 Material[]
→ 403 FORBIDDEN   // instructor is not assigned to this subject
→ 404 NOT_FOUND
```

Ordering: server decides. Current frontend does not sort; it renders in the order it receives, so use upload order (oldest first) or most-recent first consistently.

### 7.4 `POST /subjects/:subjectId/materials`

Upload a new material. Used by `src/services/uploadService.js → uploadMaterial()` and `src/services/subjectService.js → addSubjectMaterial()`.

**Role:** `instructor` (must be on the subject's roster).
**Content-Type:** `multipart/form-data`.
**Form fields:**

| Name | Required | Notes |
|---|---|---|
| `file` | yes | The binary. |
| `name` | no | Override display name; default is `file.name`. |

**Response** `201 Created`:

Returns a full `Material` object. Immediately after upload:

- `status` MUST be `"indexing"`.
- `uploadedById` MUST be the caller's user id.
- `id`, `name`, `size`, `date`, `uploadedByName`, `uploadedByInitials` MUST be populated.

The server is responsible for parsing + embedding the document. Once indexing finishes, the row flips to `status: "processed"`. The frontend currently polls `GET /subjects/:subjectId/materials` on demand; consider exposing a webhook / SSE stream later. If you need an interim contract, the frontend already tolerates:

- A short polling loop (subject page re-fetches on mount and after every mutation).
- The material appearing as `"indexing"` and then `"processed"` on the next GET.

Duplicate uploads (same `name` in the same subject) MAY be accepted (treated as new material) OR rejected with `409 CONFLICT`; the frontend handles both gracefully via toasts.

### 7.5 `PATCH /subjects/:subjectId/materials/:materialId`

Partial update. Today the frontend only flips status (e.g. forcing a re-index). Accepted fields:

| Field | Type | Notes |
|---|---|---|
| `name` | string | Rename. |
| `status` | `"indexing" \| "processed"` | Trigger a re-index by setting to `"indexing"`. Server MAY reject admin-only transitions. |

```
PATCH /subjects/data-structures/materials/M-DS-1
body: { "status": "indexing" }
→ 200 Material
```

### 7.6 `DELETE /subjects/:subjectId/materials/:materialId`

**Role:** `instructor` on the subject's roster OR `admin`.

Soft-delete is acceptable server-side; the frontend just expects the row to disappear from subsequent GETs. Historical materials whose `uploadedById` no longer matches an active instructor MUST still be returned (display as "Unknown instructor" if the id is unresolved).

```
DELETE /subjects/data-structures/materials/M-DS-1
→ 204 No Content
→ 403 FORBIDDEN
→ 404 NOT_FOUND
```

---

## 8. Chat

Two surfaces: **document chat** (students upload ad-hoc files and talk to them) and **tutor chat** (students ask questions scoped to a specific subject's materials).

### 8.1 Shared concepts

**Message shape** (what the frontend expects to render):

```json
{
  "id": "msg_01HYZ…",
  "role": "user" | "assistant" | "doc",
  "text": "The assistant or user message body, markdown allowed.",
  "createdAt": "2026-03-15T14:23:00.000Z"
}
```

- `role`:
  - `user` for messages from the human.
  - `assistant` for AI in tutor chat.
  - `doc` for AI in document chat (the frontend renders both as "assistant" UI; the distinction is purely semantic).
- `text` MUST be a string. Newlines, Markdown, bullet lists are supported client-side (`whitespace-pre-wrap`).
- If you use streaming responses (see §8.4) each SSE event contains a text delta; the frontend already simulates streaming from a complete reply, so non-streaming is fine for v1.

**Conversation shape:**

```json
{
  "id": "conv_…",
  "title": "Chat 1",
  "subjectId": "data-structures" | null,
  "createdAt": "…",
  "updatedAt": "…",
  "messageCount": 7
}
```

- `title` — derived server-side (first user message truncated, or the literal `"Chat N"` for a brand-new empty conversation). Max 120 chars.
- `subjectId` — set for tutor chats; `null` for document chats.

### 8.2 Document chat

Consumed by `useChat.js` + `sendDocMessage()`.

#### 8.2.1 Create a document chat

```
POST /chat/doc/conversations
body (multipart/form-data):
  files[]: File   // 1..5 files, see §8.2.2 for constraints
→ 201 { "conversation": Conversation, "files": DocumentFile[] }
```

`DocumentFile` shape:

```json
{
  "id": "f_…",
  "name": "notes.pdf",
  "status": "processing" | "ready",
  "sizeBytes": 18342,
  "mime": "application/pdf"
}
```

File constraints for document chat (slightly looser than material uploads):

- Allowed extensions: `.pdf`, `.pptx`, `.png`.
- Allowed MIME: `application/pdf`, `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `image/png`.
- Max size: **25 MiB per file**, max 5 files per conversation.
- Reject oversized files with `413 FILE_TOO_LARGE`.

Server processes / indexes each file asynchronously. Return immediately with `status: "processing"`. The frontend polls (or opens an SSE stream if §8.2.4 is implemented) until all are `ready`.

#### 8.2.2 Add a file to an existing document chat

```
POST /chat/doc/conversations/:conversationId/files
body (multipart/form-data): file: File
→ 201 DocumentFile
```

Same validation as above. Server MUST enforce the 5-file cap and reject with `409 CONFLICT` / `code: "FILE_LIMIT"`.

#### 8.2.3 Remove a file

```
DELETE /chat/doc/conversations/:conversationId/files/:fileId
→ 204 No Content
→ 409 CONFLICT   // if removing the last file; frontend never sends this, but enforce defensively
```

#### 8.2.4 Check file processing status (optional but recommended)

```
GET /chat/doc/conversations/:conversationId/files
→ 200 DocumentFile[]
```

#### 8.2.5 Send a message

Used by `sendDocMessage()` today as `POST /chat/doc { message }`. The refined, final contract is:

```
POST /chat/doc/conversations/:conversationId/messages
body: { "message": "string, 1..4000 chars" }
→ 200 {
  "userMessage": Message,
  "reply": {
    "id": "msg_…",
    "role": "doc",
    "text": "AI answer",
    "createdAt": "…"
  }
}
```

- Empty / whitespace-only `message` ⇒ `400 VALIDATION_ERROR`.
- If the conversation has any file still in `"processing"` state, return `409 CONFLICT` with `code: "FILES_NOT_READY"`.
- Server MUST persist both the user message and the AI reply, in order, before returning.

**Back-compat note.** If you prefer to keep the current simpler contract for v1, the minimum the frontend needs is:

```
POST /chat/doc
body: { "message": "…" }
→ 200 { "reply": "string" }
```

In that case, conversation history is ephemeral (reset on page refresh). This matches the current UX; wire the full conversation API when persistence is required.

#### 8.2.6 Streaming reply (optional)

If you implement Server-Sent Events:

```
POST /chat/doc/conversations/:id/messages
Accept: text/event-stream
```

Event format:

```
event: token
data: {"delta":"Hello"}

event: token
data: {"delta":" world"}

event: done
data: {"messageId":"msg_…"}
```

The frontend does not consume SSE today, so non-streaming is acceptable for v1.

### 8.3 Tutor chat

Consumed by `useTutorChat.js` + `sendTutorMessage(subjectId, message)`.

#### 8.3.1 Send a message

Current contract:

```
POST /chat/tutor/:subjectId
body: { "message": "string, 1..4000 chars" }
→ 200 { "reply": "string" }
```

Final recommended contract (mirrors document chat):

```
POST /chat/tutor/conversations
body: { "subjectId": "data-structures" }
→ 201 Conversation

POST /chat/tutor/conversations/:conversationId/messages
body: { "message": "…" }
→ 200 { "userMessage": Message, "reply": Message }
```

- The subject MUST exist and MUST be visible to the student (see §6.2).
- At least one material in the subject MUST have `status: "processed"`; otherwise return `409 CONFLICT` with `code: "SUBJECT_NOT_READY"` and `message: "This subject has no indexed materials yet."`.
- Empty message ⇒ `400 VALIDATION_ERROR`.

#### 8.3.2 List / load conversations

Chat history sidebar currently ships with placeholder labels (`Chat 1`, `Chat 2`, …). To make it real:

```
GET /chat/tutor/conversations?subjectId=data-structures&page=1&pageSize=20
→ 200 { items: Conversation[], page, pageSize, total, totalPages }

GET /chat/tutor/conversations/:conversationId/messages?page=1&pageSize=50
→ 200 { items: Message[], page, pageSize, total, totalPages }
```

Same shape for the document chat sidebar: `/chat/doc/conversations` without `subjectId`.

#### 8.3.3 Delete a conversation

```
DELETE /chat/tutor/conversations/:conversationId
DELETE /chat/doc/conversations/:conversationId
→ 204 No Content
```

### 8.4 Feedback (thumbs up / down on AI messages)

Used to build the admin feedback reports (§10.3). Not yet wired to a button in the UI, but the admin panel already renders stored feedback rows, so the write path MUST exist.

```
POST /chat/messages/:messageId/feedback
body: { "feedback": "up" | "down" }
→ 200 { "id": "fb_…", "messageId": "msg_…", "feedback": "up", "createdAt": "…" }
→ 409 CONFLICT   // if feedback already given — allow overwrite by returning existing id, or reject
```

`DELETE /chat/messages/:messageId/feedback` clears it.

Server MUST ensure that only the message's owner (the student who sent the preceding prompt) can leave feedback.

---

## 9. Users (current user & profile)

The frontend currently only reads the user object returned at login. A `GET /auth/me` endpoint (see §4.3) is recommended. If you extend profiles, follow:

**User shape (student / instructor / admin):**

```json
{
  "id": "U003",
  "username": "instructor",
  "name": "Dr. Nour Farid",
  "email": "nour@docmind.edu",
  "role": "instructor",
  "status": "active" | "disabled",
  "registeredAt": "2025-08-15T09:00:00.000Z",
  "lastActive": "2026-03-15T11:20:00.000Z"
}
```

Constraints:

| Field | Required | Constraints |
|---|---|---|
| `id` | yes | opaque, unique |
| `username` | yes | 1..64 chars, unique, case-sensitive |
| `name` | yes | 1..120 chars |
| `email` | yes | valid email, unique (case-insensitive) |
| `role` | yes | `student \| instructor \| admin` |
| `status` | yes | `active \| disabled`. `disabled` users cannot log in → `401 UNAUTHENTICATED`. |
| `registeredAt` | yes | ISO-8601 |
| `lastActive` | yes | ISO-8601; server updates on every authenticated call |

---

## 10. Admin endpoints

All endpoints in this section require `role=admin`. Any other role MUST get `403 FORBIDDEN`.

### 10.1 `GET /admin/users`

Used by `ManageUsers.jsx`.

**Query params:** standard pagination + `search` (matches `name`, `email`, `id`) + `role` filter (`student | instructor | admin | all`).

**Response element:** full `User` shape from §9. The page currently renders `id, name, email, role, status, registeredAt, lastActive`.

```
GET /admin/users?page=1&pageSize=8&search=sara&role=student
→ 200 { items: User[], page, pageSize, total, totalPages }
```

### 10.2 `PATCH /admin/users/:userId`

Toggle a user's status (used by the "Enable" / "Disable" button).

```
PATCH /admin/users/U004
body: { "status": "disabled" }
→ 200 User
→ 422 UNPROCESSABLE   // e.g. admin disabling themselves
```

Validation:

- `status` required, enum `active | disabled`.
- Server MUST reject an admin disabling their own account (`422 UNPROCESSABLE` with `code: "CANNOT_DISABLE_SELF"`).
- MUST append to the activity log (§10.5), action `"Account disabled"` / `"Account enabled"`, `user` = display name.

Additional admin-only write endpoints (recommended for v1.1, frontend does not yet call them):

```
POST   /admin/users           body: { username, name, email, role, password }
PATCH  /admin/users/:userId   body: partial (name, email, role, …)
DELETE /admin/users/:userId
POST   /admin/users/:userId/reset-password  body: { password } | response: generated temp password
```

### 10.3 `GET /admin/subjects/stats`

Used by `ManageSubjects.jsx` and `Analytics.jsx`.

**Response element shape:**

```json
{
  "id": "data-structures",
  "name": "Data Structures",
  "instructorIds": ["U003", "U005"],
  "semester": "spring-2026",
  "interactions": 1243,
  "aiResponses": 1198,
  "thumbsUp": 1021,
  "thumbsDown": 72
}
```

| Field | Required | Notes |
|---|---|---|
| `id` | yes | Subject slug. |
| `name` | yes | Display title. |
| `instructorIds` | yes | Array (MAY be empty). |
| `semester` | yes | One of the ids from `GET /semesters`. |
| `interactions` | yes | Total user messages (including failures). Integer ≥ 0. |
| `aiResponses` | yes | Total AI replies successfully served. |
| `thumbsUp` | yes | Count of positive feedback. |
| `thumbsDown` | yes | Count of negative feedback. |

```
GET /admin/subjects/stats
→ 200 SubjectStats[]
```

Bare array is fine; the current dataset (~9 rows) fits.

### 10.4 `GET /admin/feedback`

Used by the feedback panel + PDF report generator.

**Response element shape:**

```json
{
  "id": "F001",
  "student": "Ahmed Hassan",
  "studentId": "U001",
  "subject": "Data Structures",
  "subjectId": "data-structures",
  "semester": "spring-2026",
  "question": "What is the difference between a stack and a queue?",
  "aiResponse": "A stack follows LIFO …",
  "feedback": "up" | "down",
  "timestamp": "2026-03-15T14:23:00.000Z"
}
```

Current frontend uses `subject` (display name) and `semester` for filtering; adding `subjectId` / `studentId` future-proofs deeper links.

Filters (query params, all optional, all AND-combined):

| Param | Type | Matches |
|---|---|---|
| `semester` | string | exact match |
| `subjectId` | string | exact match |
| `feedback` | `up \| down` | exact match |
| `search` | string | partial in `question` / `aiResponse` |

```
GET /admin/feedback?semester=spring-2026&feedback=down
→ 200 Feedback[]
```

Large results MUST be paginated (`page`, `pageSize`).

### 10.5 `GET /admin/activity`

Used by the "Recent Activity" card on `AdminDashboard`.

**Response element shape (min):**

```json
{
  "id": "A001",
  "action": "New student registered",
  "user": "Nadia Saleh",
  "time": "2 min ago",
  "createdAt": "2026-03-15T13:55:00.000Z"
}
```

- `action` — short sentence describing the event.
- `user` — display name of the actor or subject of the action.
- `time` — pre-formatted relative string. Optional if `createdAt` is provided (frontend may format itself in future).
- `createdAt` — ISO-8601. Preferred.

Events to log (non-exhaustive — add as features grow):

- `"New student registered"` / `"New instructor added"` / `"New admin added"`
- `"Material uploaded"` / `"Material deleted"`
- `"Subject created"` / `"Subject updated"` / `"Subject deleted"`
- `"Account enabled"` / `"Account disabled"`
- `"AI response flagged"` (when feedback=`down` is submitted)
- `"Student access enabled"` / `"Student access disabled"`

```
GET /admin/activity?limit=20
→ 200 Activity[]
```

Default limit: 20. Ordering: most recent first.

### 10.6 `GET /admin/analytics/daily`

Used by the "Daily Usage Trends" line chart.

**Response element shape:**

```json
{
  "date": "Mar 14",
  "isoDate": "2026-03-14",
  "conversations": 85,
  "questions": 260
}
```

- `date` — short label for the X-axis (e.g. `"Mar 14"`). Pre-formatted.
- `isoDate` — ISO-8601 date-only (`YYYY-MM-DD`). Preferred; allows client-side re-formatting.
- `conversations` — integer ≥ 0. Distinct chat sessions started that day.
- `questions` — integer ≥ 0. User messages sent that day (across doc + tutor chats).

**Query params (optional):** `range` = `7d | 14d | 30d | all`. Default `14d`. If `all`, return every row the server has.

```
GET /admin/analytics/daily?range=14d
→ 200 DailyUsage[]
```

### 10.7 Feedback report

The PDF is generated client-side (`generateFeedbackReport.js`). The backend does not need to produce PDFs; it only needs `/admin/subjects/stats` and `/admin/feedback` to be correct.

---

## 11. Uploads (generic endpoint, deprecated)

The frontend's `src/services/uploadService.js` exposes `uploadDocument()` and `uploadMaterial()`. The recommended final routing is:

- `uploadMaterial(subjectId, file)` → `POST /subjects/:subjectId/materials` (see §7.4).
- `uploadDocument(file)` → `POST /chat/doc/conversations` (see §8.2.1) or a dedicated `POST /uploads/document` if you want separation of concerns. If you go with the dedicated route, return:

```json
{
  "id": "f_…",
  "name": "notes.pdf",
  "status": "processing" | "ready",
  "sizeBytes": 18342
}
```

Any generic `/uploads/*` endpoint MUST enforce the same size / MIME / virus-scan rules as §7.2.

---

## 12. Security checklist (mandatory)

- [ ] Passwords hashed with bcrypt/argon2; no plaintext, no reversible encryption.
- [ ] JWT secrets (or RSA keys) loaded from environment, not committed.
- [ ] `Authorization` header required on all non-public endpoints (public endpoints: `GET /health`, `POST /auth/login`, `GET /system/student-access`).
- [ ] Rate limiting on `POST /auth/login` and chat / upload endpoints.
- [ ] Request-size limit of at minimum 60 MiB on upload endpoints (to accept 50 MiB files + multipart overhead) and 1 MiB on JSON endpoints.
- [ ] All file uploads virus-scanned before indexing.
- [ ] PDF parsing library is hardened (CVE-watched).
- [ ] CORS restricted to the known frontend origin(s).
- [ ] HTTPS enforced in prod; `Strict-Transport-Security` header set.
- [ ] Role checks on EVERY endpoint, not relying on URL prefix alone.
- [ ] `studentAccess.enabled=false` enforced on login AND on every student-scoped endpoint call.
- [ ] Users cannot edit resources outside their scope: instructors only their subjects' materials; students only their own conversations / feedback.
- [ ] No endpoint leaks whether a user exists (login and password-reset use generic errors).
- [ ] All writes produce an activity-log entry when they are admin-visible actions (§10.5).

---

## 13. Environment variables (frontend ↔ backend contract)

| Frontend env var | Default | Used at |
|---|---|---|
| `VITE_API_BASE_URL` | `/api` | `src/services/apiClient.js` — prepended to every request path. |

The backend SHOULD be mounted so that the frontend can point `VITE_API_BASE_URL` at a single origin (e.g. `https://api.docmind.example.com/api`). All paths in this document are relative to that base URL (so `/auth/login` becomes `https://api.docmind.example.com/api/auth/login`).

---

## 14. Minimum endpoint list for frontend parity (v1)

If you only build these, the current UI works with real data end-to-end:

1. `POST /auth/login`
2. `POST /auth/logout`
3. `GET /system/student-access`
4. `PATCH /admin/system/student-access`
5. `GET /subjects/student`
6. `GET /subjects/instructor`
7. `GET /subjects/:id`
8. `GET /subjects/:id/instructors`
9. `GET /subjects/:id/materials`
10. `POST /subjects/:id/materials`
11. `PATCH /subjects/:id/materials/:materialId`
12. `DELETE /subjects/:id/materials/:materialId`
13. `POST /chat/doc` **OR** the full `/chat/doc/conversations/*` stack
14. `POST /chat/tutor/:subjectId` **OR** the full `/chat/tutor/conversations/*` stack
15. `GET /admin/users`
16. `PATCH /admin/users/:id`
17. `GET /admin/subjects/stats`
18. `GET /admin/feedback`
19. `GET /admin/activity`
20. `GET /admin/analytics/daily`
21. `GET /semesters`

Everything else in this document is recommended polish: conversation persistence, per-message feedback, `/auth/me`, streaming, user creation, etc.

---

## 15. Reference: role → endpoint matrix

Legend: ✅ allowed, ❌ forbidden (returns `403`), 🔒 subject to `STUDENT_ACCESS_DISABLED` when the global flag is off.

| Endpoint | student | instructor | admin |
|---|---|---|---|
| `POST /auth/login` | ✅ (🔒 blocked at login) | ✅ | ✅ |
| `POST /auth/logout` | ✅ | ✅ | ✅ |
| `GET /auth/me` | ✅ | ✅ | ✅ |
| `GET /system/student-access` | ✅ (public) | ✅ (public) | ✅ (public) |
| `PATCH /admin/system/student-access` | ❌ | ❌ | ✅ |
| `GET /subjects/student` | 🔒 | ❌ | ❌ |
| `GET /subjects/instructor` | ❌ | ✅ (only own) | ✅ |
| `GET /subjects/:id` | 🔒 | ✅ | ✅ |
| `GET /subjects/:id/instructors` | 🔒 | ✅ | ✅ |
| `GET /subjects/:id/materials` | ❌ | ✅ (must be on roster) | ✅ |
| `POST /subjects/:id/materials` | ❌ | ✅ (must be on roster) | ❌ |
| `PATCH /subjects/:id/materials/:mid` | ❌ | ✅ (must be on roster) | ✅ |
| `DELETE /subjects/:id/materials/:mid` | ❌ | ✅ (must be on roster) | ✅ |
| `POST /chat/doc/**` | 🔒 | ❌ | ❌ |
| `POST /chat/tutor/**` | 🔒 | ❌ | ❌ |
| `POST /chat/messages/:id/feedback` | 🔒 (only on own message) | ❌ | ❌ |
| `GET /admin/**` | ❌ | ❌ | ✅ |
| `GET /semesters` | ❌ | ❌ | ✅ |
| `GET /health` | ✅ (public) | ✅ (public) | ✅ (public) |

---

## 16. Change log

| Version | Date | Notes |
|---|---|---|
| 1.0 | 2026-04-18 | Initial specification. Guest / anonymous access paths have been removed from the frontend and MUST NOT be implemented on the backend. |
