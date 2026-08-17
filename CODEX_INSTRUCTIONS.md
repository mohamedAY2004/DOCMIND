# Handover cleanup — instructions for Codex

Goal: make the repo handover-ready for a new team. The code itself was reviewed
and needs **no cleanup pass** — these tasks fix documentation drift, repo
hygiene, and two small code modernizations. Do the tasks in order; each task is
its own commit. Do **not** push.

## Ground rules

- Backend runs in the `mini-rag` conda env (Python 3.10):
  `C:\Users\mohamed\miniconda3\envs\mini-rag\python.exe`. Never use the base env.
- Backend tests: `cd backend/src && pytest -q`. They need Postgres+pgvector on
  host port 5433 (`cd backend/docker && POSTGRES_PORT=5433 docker compose up -d postgres`)
  and test deps from `backend/src/requirements-test.txt`. See `backend/src/tests/README.md`.
- Frontend checks: `cd frontend && npm run lint && npm run build`.
- Never read or commit real `.env` files (a repo hook enforces this). `.env.example` files are fine.
- Stay on `main`. Do not push. Do not amend existing commits.
- **Out of scope — do not do:** refactoring/splitting the large frontend admin
  pages, deleting the legacy backend surface, implementing the mobile TODO
  stubs, or any behavior change beyond Task 5.

## Task 1 — Establish a green baseline, then commit the pending work

There are ~78 modified files (+4220/−908) sitting uncommitted. Turn them into
clean history **before** making any new changes.

1. Run the backend test suite and frontend lint/build. All must pass before you
   commit anything. If something fails, stop and report — do not "fix" pending
   work you don't understand.
2. Read `git status` and `git diff` per file (skim is fine) and group the
   changes into **3–8 thematic commits**. Group by surface and feature, e.g.:
   backend chat/feedback changes together, backend RAG/store changes together,
   frontend chat UI together, admin pages together, mobile DTO alone,
   `portal-demo/` alone, config/`.gitignore`/`.env.example` together. Derive
   the real grouping from the diffs — the list above is a hint, not a spec.
3. Write commit messages that describe **what changed and why**, in the style
   of the existing history (`git log --oneline -10`). One-line subject,
   optional body.
4. Do not commit files you cannot explain from the diff — list any such file in
   your final report instead.

**Done when:** `git status` is clean, tests/lint still pass, and `git log`
shows the thematic commits.

## Task 2 — Fix stale claims in CLAUDE.md

`CLAUDE.md` contradicts the repo in three places. Fix only these; leave the
rest of the file alone.

1. **Test deps block (Commands → Backend section).** It currently says test
   deps "are NOT in requirements.txt — install them explicitly" with pinned
   `pip install pytest==8.* ...`. Replace with the real workflow:
   `pip install -r requirements-test.txt` (file exists at
   `backend/src/requirements-test.txt`), and note tests need Postgres on port
   5433 with a pointer to `backend/src/tests/README.md`.
2. **"Tests are intentionally thin right now (`tests/test_errors.py`,
   `tests/test_file_service.py`); DB-dependent tests are a planned follow-up."**
   This is false — there are ~35 integration test files covering every
   non-legacy endpoint against real Postgres with faked LLM providers. Replace
   the sentence with an accurate one-liner and point to
   `backend/src/tests/README.md` for the harness details.
3. **Rerank paragraph (RAG pipeline section).** It says `sentence-transformers`
   is "kept out of `requirements.txt` to keep the image lean". It is now pinned
   in `backend/src/requirements.txt` (line 29, `sentence-transformers == 5.6.0`).
   Update the sentence (the lazy-import claim is still true and stays). While
   there, normalize line 29's spacing to `sentence-transformers==5.6.0` to
   match the rest of the file.

**Done when:** every command and claim you touched is verifiably true against
the repo.

## Task 3 — Archive historical review docs

The repo root mixes current guidance with one-off review artifacts. A new team
can't tell which is which.

1. Create `docs/archive/`.
2. `git mv` these three files into it: `BACKEND_DEEP_REVIEW.md`,
   `CODEX_REVIEW.md`, `RAG_PIPELINE_CHANGES.md`.
3. Add a 3-line `docs/archive/README.md` saying these are historical
   review/changelog snapshots, not current guidance.
4. **Keep at root:** `README.md`, `CLAUDE.md`, `PILOT_DEPLOYMENT.md` (current
   ops doc), and this file.
5. Grep the repo for references to the moved filenames and update any links.

## Task 4 — Document the legacy backend surface

The legacy debug surface (`backend/src/controllers/`,
`backend/src/routes/legacy_router.py`, the raw asyncpg pool in `main.py`,
routes `/api/v1/data/*` and `/api/v1/nlp/*`) is quarantined but its status
isn't written down anywhere a new team would look.

Add a short section "Legacy debug surface" to `backend/README.md` stating:

- What it is and where it lives (the paths above).
- It is a dev-only tool for poking the RAG pipeline; not part of the official
  API; intentionally excluded from the test suite.
- Rule: never add new code there (matches CLAUDE.md).
- Deletion criteria: it can be removed once no developer workflow depends on
  the `/api/v1/*` debug routes; removing it also removes the second asyncpg DB
  path in `main.py`. (Do **not** delete anything yourself.)

## Task 5 — Migrate FastAPI startup/shutdown to lifespan

`backend/src/main.py` uses the deprecated `@app.on_event("startup")` /
`@app.on_event("shutdown")` pair. Replace both with a single
`@asynccontextmanager` `lifespan` function passed to `FastAPI(...)`.

- Move the startup body before `yield`, the shutdown body after. Preserve
  behavior and ordering exactly — including the `app.state` mirroring and the
  try/except around the token-blocklist purge.
- Check `backend/src/tests/conftest.py` first: if the test harness builds its
  own app or triggers startup differently, adapt so tests still exercise the
  same init path.
- **Done when:** full backend suite passes and no `on_event` remains.

## Task 6 — Inline-style cleanup (frontend)

House rule is Tailwind-only, no `style={{}}`. Convert the **static** inline
styles to Tailwind arbitrary values; leave the genuinely dynamic ones.

- Convert: the two radial-gradient overlays in
  `frontend/src/components/ui/AuthCard.jsx`, and any static styles in
  `frontend/src/components/ui/GradientBackdrop.jsx` and
  `frontend/src/components/ui/ProcessingState.jsx` (inspect each — convert only
  values that are compile-time constants; CSS `var(...)` inside an arbitrary
  value is fine, e.g. `bg-[radial-gradient(...)]`).
- Leave as-is (runtime values): `InstructorSubject.jsx` upload-progress width,
  `features/analytics/CustomTooltip.jsx` series color.
- Verify visually if you can run the dev server; at minimum `npm run lint`
  and `npm run build` must pass and the generated class must appear in the
  built CSS.

## Task 7 — Mobile status note

The mobile app is the least mature surface (single "Add Mobile App Repo"
commit; the repo's only TODOs live there). Make that explicit so a new team
isn't surprised.

Add a "Current status" section to `mobile/docmind_app/README.md`:

- Working features vs. stubbed ones. Known stubs: `profile` serves static user
  data (`TODO(backend)` in
  `lib/features/profile/presentation/controllers/profile_controller.dart`),
  `subject_tutors` uses a fake datasource (`TODO(backend)` in
  `lib/features/subject_tutors/domain/usecases/get_subjects_usecase.dart`),
  and Privacy / Help & Support navigation is unimplemented (`TODO(nav)`).
- One line: backend and web frontend are production-grade; mobile is a
  work-in-progress that lags the backend API.
- Do **not** implement any of the stubs.

## Final report

When done, report: the commit list from Task 1 with one-line rationale each,
any files you could not confidently commit, test/lint results before and
after, and anything you found that contradicts these instructions.
