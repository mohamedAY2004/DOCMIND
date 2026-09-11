# DocMind maintainability review

Reviewed 2026-09-05 against working tree at `2498dbd829487b6794338454a1ec4b0c28b55777`.

The highest-value cleanup is to repair and consolidate contracts that already disagree: provider behavior, subject authorization, chat request lifetimes, and client response mapping. Dead code exists, but deleting it alone will leave the main maintenance risks intact.

This is a whole-project review, not a comparison against an earlier commit. Application code was not changed. The existing untracked agent/configuration and handover files were preserved. This document is a dated review snapshot, not a replacement for current agent guidance.

## Scope and verification

The source inventory covered 174 backend Python files, 105 frontend JS/JSX files, and 90 mobile Dart library files. Counts exclude tests and caches; backend counts include migrations and scripts. Review combined route/import/call-site tracing, targeted implementation reading, cross-client contract comparisons, and executable checks. File size was used to locate candidates, not as proof that a module needs splitting.

- Backend: **168 tests passed**, using the `mini-rag` Python environment and the dedicated PostgreSQL test database; `pytest tests -q -p no:cacheprovider` completed in 71.09 seconds.
- Frontend: lint and production build passed; **7 test files / 11 tests passed**. Build warnings include a 616.93 kB minified chunk and stale Browserslist data.
- Additional backend checks with fakes reproduced missing preview membership checks, discarded vector-write failure, Cohere constructor failure, and Qdrant ID conversion failure. These checks made no external provider calls.
- Two temporary frontend hook tests reproduced stream continuation after unmount and stale error/retry state after switching conversations. They failed the expected-behavior assertions and were removed after review.
- Mobile: static route/import/DI tracing and backend contract comparison completed. Flutter/Dart were unavailable in the inspected environment, so analyzer and mobile tests were not run.

Passing existing checks does not establish provider interchangeability, application startup correctness, or full client lifecycle correctness. The backend fixture substitutes providers and skips lifespan; mobile CI runs only the DTO contract test.

Priorities: **P1** = address before exposing the affected surface; **P2** = important correctness or maintainability work; **P3** = bounded cleanup. “Documented violation” refers to an explicit repository rule. “Design judgment” identifies a proposed structure, not an objective style defect.

## Findings

### 1. [P1] The legacy debug API is live and unauthenticated

**Evidence:** `backend/src/main.py:225–226`, `routes/legacy_router.py:13–17`, `routes/data.py:18–26`, `routes/nlp.py:12–19`; all shorthand paths here are under `backend/src/`.

The application always mounts `/api/v1/data/*` and `/api/v1/nlp/*`. These routers do not require authentication, yet support uploads, indexing/resetting legacy collections, searching, and generation through the shared providers. The chat/upload rate-limit patterns in `helpers/middleware.py:19–28` exclude these paths. “Internal” is an OpenAPI tag, not an access restriction.

**Action:** default-disable this surface through an explicit development setting, or move it into a separate debug application. If it shares a deployment, apply an explicit admin access policy. Confirm developer workflows before deleting its implementation.

**Acceptance:** the production app does not expose these routes; an intentionally enabled debug deployment applies the chosen authentication policy. These controllers/models are **live legacy code**, not confirmed dead code.

### 2. [P1] Duplicated preview authorization permits access to another subject

**Evidence:** `backend/src/routes/materials_router.py:265–273`; compare the roster check at `:179–180`.

The nonstreaming test-bot route checks role, subject existence, semester status, and processed materials, but never checks instructor membership. The streaming route does check membership. An instructor can call the nonstreaming endpoint for another active subject. An isolated invocation with membership denied still returned the other subject's content; the membership method was called zero times.

**Action:** move preview preparation, authorization, and generation into one service used by both transports. Move `_TestBotRequest` and `_TestBotResponse` out of the router into `schemas/`. This is also a documented Route → Service → Repository violation.

**Acceptance:** an unrelated instructor is denied by both routes; assigned instructors and admins retain the intended access.

### 3. [P1] The mobile HTTP client logs sensitive request and response data

**Evidence:** `mobile/docmind_app/lib/core/network/dio_client.dart:18–24`.

The shared client enables request headers, request bodies, and response bodies without an environment guard or redaction. Login passwords, bearer headers, returned tokens, and document/chat content flow through this client.

**Action:** restrict diagnostic logging to development and redact credentials; omit sensitive bodies. Keep this policy in the shared HTTP client so individual features cannot drift.

**Acceptance:** inspect representative login and chat logs and verify that passwords, tokens, authorization headers, and sensitive payloads are absent.

### 4. [P2] Indexing reports success when vector persistence fails

**Evidence:** `backend/src/services/rag_service.py:127–134`; `stores/vectordb/providers/PgVectorProvider.py:198–207`, `QdrantDBProvider.py:93–97`; `services/material_service.py:425–428`, `document_chat_service.py:680–684`.

`index_chunks()` ignores the Boolean returned by `insert_many()` and returns the number of chunks. Both providers can catch persistence errors and return `False`. Callers then mark the upload processed/ready despite missing or partial vectors. A one-chunk fake write returning `False` still returned an indexed count of `1`.

**Action:** define a single explicit write-failure contract: a provider exception or typed write result. Transition to ready only after successful persistence. Do not blindly reject every `False`: `create_collection(False)` currently also means the collection already exists.

**Acceptance:** failed and partial writes cannot produce ready uploads; failures remain observable and retryable.

### 5. [P2] Advertised providers do not satisfy the same contract

**Evidence:** `backend/src/stores/llm/LLMProviderFactory.py:23–28`, `providers/CoHereProvider.py:8–11`; `backend/src/stores/vectordb/providers/QdrantDBProvider.py:152–154`; `backend/src/services/rag_service.py:120–121`.

Two failures were reproduced without a provider network call:

- Cohere's factory passes `default_generation_max_tokens` and `default_temperature`; its constructor accepts different names. Selecting `COHERE` raises `TypeError` during construction.
- Qdrant converts record IDs as hexadecimal UUIDs. Official ingestion generates opaque strings such as `tutor_example_0123456789abcdef_0`, which raise `ValueError` in that conversion.

**Action:** align constructor vocabulary and map opaque vector IDs deterministically, for example through UUID5. Add small factory and index/search/delete contract checks for every advertised provider. The documented configuration-only provider switch should actually work.

**Acceptance:** each factory constructs its selected adapter, and each vector adapter accepts IDs emitted by official ingestion.

### 6. [P2] Duplicate chat hooks allow an old stream to update the new conversation

**Evidence:** `frontend/src/hooks/useChat.js:144–153`, `useTutorChat.js:167–174`; effect cleanup at `useChat.js:83` and `useTutorChat.js:90`.

Both hooks independently implement events, cancellation, retry text, and loading state. On A → B navigation, aborting A still allows A's catch/finally handlers to write into B's state. Unmount cleanup only invalidates history loading and does not abort an active generation. Two temporary tests reproduced both defects.

**Action:** consolidate the shared generation lifecycle into one hook/reducer with request-identity guards for events, catch, and finally. Abort on cleanup and keep document/tutor adapters thin. Retain regression tests for navigation, unmount, cancellation, and a new request starting before the old one settles.

**Acceptance:** all state updates belong to the current conversation/request; leaving a chat stops its client stream. Extraction is a design judgment; the stale state updates are reproduced defects.

### 7. [P2] API adapters discard pagination and conceal incomplete history

**Evidence:** `frontend/src/services/chatService.js:48–64`, `:155–173`; `backend/src/repositories/message_repository.py:80–94`.

Chat services flatten page responses into arrays. Hooks request the default first page: 20 conversations or 50 messages. Messages are sorted ascending, so reopening a long chat exposes its first 50 messages with no mechanism to retrieve the rest. Several admin pages instead fetch a first page capped at 1,000 and calculate local totals, e.g. `frontend/src/pages/admin/ManageUsers.jsx:98–103`.

There are also 11 `unwrapList` definitions distributed across services, pages, components, and analytics. Unexpected responses commonly become `[]`, making a contract error look like a legitimate empty result.

**Action:** define and preserve a page result at the service interface. Give lists/history explicit next-page behavior. Normalize compatibility shapes once in the service layer; reject malformed responses instead of silently hiding them.

**Acceptance:** users can reopen messages beyond the first 50 and reach conversations beyond the first 20. UI code consumes one documented shape without transport-specific branches.

### 8. [P2] Async conversation and material loaders are not scoped to their subject

**Evidence:** `frontend/src/hooks/useConversations.js:30–40`, `:49–52`; `frontend/src/pages/InstructorSubject.jsx:118–125`, `:164–218`.

Changing `signalKey` starts a new conversation request without invalidating the previous one. A slow request for subject A can overwrite B's list and auto-select A's conversation. The hook claims cancellation on unmount but has no cleanup. Material refresh/upload completion can similarly write to the current page after `subjectId` changes.

**Action:** use a subject/request identity and invalidate old requests in cleanup. Extract `useSubjectMaterials(subjectId)` to own loading, polling, and mutations; let the route compose permissions, lists, and dialogs. Do not adopt the unused `useAsync` hook as-is: its shared cancellation flag has a similar race.

**Acceptance:** resolve A after B in a test; A cannot change B's lists, selection, errors, or upload state.

### 9. [P2] RAG construction and preparation have multiple owners

**Evidence:** `backend/src/routes/materials_router.py:42–49`, `:303–310`; `routes/chat_tutor_router.py:35–48`; `services/tutor_chat_service.py:271–279`; `workers/evaluation_worker.py:112–119`.

The instructor preview factory omits configured reranking/MMR parameters passed by tutor chat. Preview agent calls also omit the manifest/material-index/source-filter context prepared by the student path. The preview therefore does not reliably exercise the pipeline it claims to preview. The evaluation worker imports a private route factory and fabricates an HTTP request to reuse it.

**Action:** put typed RAG construction outside routes and share subject-corpus preparation between preview, chat, and workers. Callers should pass domain context, not manufacture HTTP objects.

The document and tutor services also duplicate draft persistence, agent adaptation, completion/cancellation/failure, telemetry, and event construction in `document_chat_service.py:344–494` and `tutor_chat_service.py:368–537`. After behavior is covered, extract a common generation lifecycle with explicit prepared context. Keep subject authorization and document ownership preparation in their own services.

**Acceptance:** the same enabled retrieval settings and source scope apply to preview and student chat; worker composition has no route import. Lifecycle extraction is a design judgment, not a reason to merge all chat domain logic into one class.

### 10. [P2] Mobile has competing document-message implementations

**Evidence:** `mobile/docmind_app/lib/features/live_chat/domain/usecases/send_message_usecase.dart:13–18`; `features/chat_with_documents/presentation/controllers/document_chat_controller.dart:370–419`.

The active send use case owns Dio, token storage, endpoints, parsing, and exceptions inside the domain layer. A second document send implementation remains in the document controller, use case, repository, and datasource. The controller's `sendMessage` and `loadMessagesForConversation` have no callers; document navigation opens `LiveChatPage`, which uses `LiveChatController`.

Controllers also construct concrete data repositories, e.g. `document_chat_controller.dart:39–47` and `live_chat_controller.dart:46–50`. This reverses the documented presentation → domain ← data dependency direction and makes dependency substitution difficult.

**Action:** route active sending through a repository interface and one response mapper. Assemble repositories/use cases in GetX bindings and inject use cases into controllers. Remove the inactive send branch after tracing its remaining model/test consumers. Preserve message reading needed by polling until finding 11 is fixed.

**Acceptance:** one active implementation of document sending; controller tests can replace use cases without initializing Dio/storage.

### 11. [P2] Mobile infers document readiness from the wrong endpoint

**Evidence:** `mobile/docmind_app/lib/features/chat_with_documents/presentation/controllers/document_chat_controller.dart:334–344`; `backend/src/services/document_chat_service.py:176–181`, `:197–205`.

Polling GET messages marks processing complete on the first successful response. That endpoint lists messages regardless of file readiness; still-processing or failed uploads can therefore appear ready. The backend already provides GET files with actual statuses, and the mobile repository contains an unused `getFileStatus` method.

**Action:** expose the files/status operation through a use case, explicitly aggregate processing/ready/failed states, and serialize polling so slow calls do not overlap.

**Acceptance:** successful history retrieval cannot mark an unfinished upload ready; failed indexing is displayed as failure.

### 12. [P2] Mobile loses message metadata and silently suppresses failures

**Evidence:** `mobile/docmind_app/lib/features/live_chat/data/repositories/live_chat_repository_impl.dart:28–34`; `features/live_chat/presentation/controllers/live_chat_controller.dart:97–98`, `:185–187`.

DTOs parse citations, generation status, and grounding status, but history mapping discards all three and the domain entity cannot carry them. Active sending separately maps only basic text/identity fields. The DTO contract test can pass while the UI never receives the richer contract. Send/history errors are also swallowed, leaving an optimistic user message with no delivery failure or retry state.

**Action:** carry message metadata through the domain entity and one mapper for send/history. Model typed failures and explicit loading/sending states; preserve the draft or mark failed delivery and offer retry.

**Acceptance:** a cited or interrupted response retains its metadata at the UI boundary; failed sends and history loads have observable, recoverable states.

### 13. [P2] Runtime vector DDL contradicts Alembic ownership

**Evidence:** `backend/src/stores/vectordb/providers/PgVectorProvider.py:44–66`, `:129–136`; `backend/src/alembic/versions/0001_initial.py:3–5`.

Provider connect creates tables/indexes and installs the extension; collection creation adds HNSW indexes. The initial migration explicitly excludes these tables. This conflicts with agent guidance and the entrypoint's claim that Alembic owns schema changes. `CREATE TABLE IF NOT EXISTS` does not migrate existing table definitions.

**Action:** move fixed vector schema/extension ownership into migrations and validate compatibility on connection. Make any necessary per-collection index provisioning an explicit, documented operation. Do not rewrite old applied migrations; add a migration that adopts existing installations safely.

**Acceptance:** both fresh and existing databases reach the intended schema through migrations. Provider connection does not silently mutate the fixed schema.

### 14. [P2] Analytics and retention bypass repositories

**Evidence:** `backend/src/services/admin_stats_service.py:36–46`, `:68–108`; `backend/src/services/retention_service.py:22–40`.

These services issue SQLAlchemy queries directly, violating the documented layer rule. Subject stats load all subjects, paginate in Python, and perform six queries for each visible subject. Data-access changes and business interpretation are coupled in the same method.

**Action:** put paginated aggregate reads in a repository, using grouped queries with a bounded query count. Keep status interpretation and expiry policy in services/pure functions. Retain the repository layer required by this project; do not remove it merely because some CRUD methods are thin.

**Acceptance:** pagination happens in the database; query count does not grow by six per returned subject; services contain no SQL query construction.

### 15. [P2] Current-looking documentation describes obsolete contracts

**Evidence:** `README.md:250–257`, `:429`; `frontend/API_SPECIFICATION.md:703`; `frontend/FRONTEND_EXPLAINED.md:882`, `:1167–1168`; `mobile/docmind_app/README.md:8–9`; `CODEX_INSTRUCTIONS.md:3–4`, `:18–20`.

Examples with direct consequences for future AI work:

- The root README lists `/api/chats/documents` and `/api/chats/tutor`; mounted routes use `/api/chat/doc/conversations` and `/api/chat/tutor/conversations`.
- The frontend spec/guide says streaming is simulated; current chat services call SSE endpoints. The guide also describes the old browser token flow instead of current cookie/refresh/CSRF handling.
- The root README says `sentence-transformers` is excluded from requirements; it is pinned there.
- Mobile status claims fake profile and subject data, but these use the stored authenticated user and a live subjects datasource.
- `CODEX_INSTRUCTIONS.md` is a completed, task-specific handover instruction file that still says no code cleanup is needed and excludes large refactors. Its constraints should not masquerade as permanent policy.
- `AGENTS.md` is untracked and largely duplicates `CLAUDE.md`; `.cursor/rules` repeats conventions again. The strict three-directive CSS rule conflicts with the live theme/vendor styles in `frontend/src/index.css` and prior task-specific dynamic-style exceptions.

**Action:** choose one version-controlled canonical agent guide, with short pointers or nonduplicated surface guidance elsewhere. Archive dated task instructions. Make one API contract source authoritative, preferably generated from application schemas/OpenAPI with separately documented SSE events and business semantics. Correct entrypoint docs and explicitly reconcile the styling rule with the working theme; do not delete functioning CSS just to satisfy a stale sentence.

**Acceptance:** a new agent can identify one active guide, real entrypoints, actual test commands, and the live browser/mobile contracts without comparing historical documents.

### 16. [P2] Existing verification misses the boundaries most likely to drift

**Evidence:** `backend/src/tests/conftest.py:3–7`, `:72–85`, `:127–151`; `.github/workflows/pilot-ci.yml:99–111`.

The backend harness bypasses lifespan and uses fakes. Its session-wide autouse schema fixture makes even the nominally pure tests require PostgreSQL. Flutter CI executes only `test/message_contract_test.dart`, omitting analysis and the app smoke test. Frontend tests currently do not protect conversation-switch/unmount behavior or cross-page pagination. Ordinary unused-variable lint does not detect unused exports and unreachable files.

**Action:** add focused checks at these actual failure seams: provider construction/contract tests, lifespan wiring with substituted resources, chat lifecycle races, pagination, mobile entity mapping/controller failures. Scope DB setup to integration tests so pure logic can run quickly. Add Flutter analysis and the whole existing test directory to CI once the baseline is addressed. Add an entrypoint-aware unused-export check and a small documented dependency-direction check.

**Acceptance:** the reproduced defects fail a permanent regression check before repair and pass afterward. Avoid broad snapshot suites or tests that merely mirror private implementation details.

## Confirmed dead-code cleanup

These are in-repository findings corroborated by symbol searches and import/route analysis. They do not assert that unpublished external scripts never import a private helper. Remove in small, reviewable changes and run the relevant existing checks.

### Backend candidates

All paths below are under `backend/src/`:

- `services/ingestion_service.py:154–159`: two consecutive `_mode` definitions; the second shadows the first and neither is called. The shadowed definition references an unimported `Counter`.
- `services/material_service.py:93–107`: `_ensure_on_roster` has no caller; active methods use other access helpers.
- `repositories/material_repository.py:27–41`: `processed_names_for_subject`; current manifest construction uses `processed_materials_for_subject`.
- `repositories/feedback_repository.py:73–86`: `count_by_subject`.
- `repositories/message_repository.py:113–121`: `count_since`.
- `repositories/subject_repository.py:198–205`: `student_count`.
- `schemas/common.py:15–20`: `ErrorBody`; keep the live `ORMModel` in the same file.
- `models/enums/DataBaseEnum.py:2–5`: unused enum library.

### Frontend candidates

All paths below are under `frontend/src/`:

- `hooks/useAsync.js`, `hooks/useStreamingText.js`, and `components/ui/InstructorAvatarGroup.jsx`: unreachable from the application entrypoint and no consuming references found.
- `components/admin/index.js`, `components/chat/index.js`, and `components/ui/index.js`: unused barrel files. **Keep live components** imported directly elsewhere.
- `services/adminService.js:19`, `:53`, `:86`: unused `getUser`, `setUserSubjects`, `getSubjectStudents` exports.
- `services/subjectService.js:56`, `:94`: unused `updateSubjectMaterial`, `sendTestBotMessage` exports. Removing an unused client function does not prove its backend endpoint is unused externally.
- `utils/formatters.js:1`: unused `formatFileSize` export.
- `components/ui/GradientBackdrop.jsx:16`: no caller uses its `gradient` escape-hatch prop. Remove that prop and branch while preserving the live preset variants.

### Mobile candidates and conditional removals

- `mobile/docmind_app/lib/core/constants/app_texts.dart` and `lib/core/theme/app_text_styles.dart`: the only two libraries unreachable in a 90-file import/export traversal; no references in library or test code.
- The unused document-controller send/history UI methods described in finding 10 are candidates after consolidating the active chat path. Do not delete every associated DTO: the current contract test uses one of them.
- `AppRoutes.documentLiveChat` has no internal navigation caller, but it is registered. Check external route/deep-link expectations before removing the alias.
- `getFileStatus` is unused but potentially useful for correcting finding 11. Resolve the readiness design before deciding to delete or activate it.

Do not classify the legacy route tree, registered providers, dynamically loaded locale templates, ORM registration imports, interface methods, or `portal-demo/` as dead solely from low reference counts. The demo is explicitly documented as a separate surface.

## Recommended implementation order

1. **Close exposed access/logging gaps:** findings 1–3. Add narrow access-policy checks and verify log output.
2. **Repair provider and indexing contracts:** findings 4–5. Keep all advertised adapters under a common behavioral check.
3. **Stabilize client state and contracts:** findings 6–8 and 10–12. Preserve pagination and metadata; scope async work to a conversation/subject.
4. **Delete confirmed unused code and correct guidance:** dead-code inventory and finding 15. These can be separate small changes, avoiding behavioral refactors in the deletion commit.
5. **Consolidate implementation ownership:** findings 9, 13, and 14, with focused verification from finding 16. Treat vector schema adoption as a migration with existing-database compatibility.

The target structure is modest: one provider composition module, one shared generation lifecycle, one response-mapping location per client, explicit async request ownership, and one canonical agent guide. Keep existing domain/service/repository separation where it earns its place. Prefer deleting competing implementations to adding another generic framework over them.
