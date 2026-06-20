<p align="center">
  <img src="frontend/src/assets/docmind-logo.png" alt="DocMind Logo" width="120" />
</p>

<h1 align="center">DocMind</h1>

<p align="center"><strong>AI-Powered Document Assistant for University Education</strong></p>

<p align="center">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react&logoColor=white" alt="React 19" />
  <img src="https://img.shields.io/badge/FastAPI-0.110-009688?style=flat&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PostgreSQL-pgvector-336791?style=flat&logo=postgresql&logoColor=white" alt="PostgreSQL + pgvector" />
  <img src="https://img.shields.io/badge/LLM-Gemini%20%7C%20OpenAI%20%7C%20Cohere-FF6F00?style=flat&logo=google&logoColor=white" alt="LLM" />
  <img src="https://img.shields.io/badge/VectorDB-pgvector%20%7C%20Qdrant-9B59B6?style=flat" alt="VectorDB" />
  <img src="https://img.shields.io/badge/License-Academic-blue?style=flat" alt="License" />
</p>

---

DocMind is a graduation project that brings AI-driven document interaction to the university environment. It enables students to chat with their course materials, get help from subject-specific AI tutors, and empowers instructors to manage and enrich their course content — all through an intuitive, modern interface backed by a production-grade RAG pipeline.

---

## Table of Contents

- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [Key Features](#key-features)
- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [API Overview](#api-overview)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Environment Variables](#environment-variables)
- [User Roles](#user-roles)
- [Data Model](#data-model)
- [AI / RAG Pipeline](#ai--rag-pipeline)
- [Academic Context](#academic-context)
- [Team](#team)
- [Academic Supervision](#academic-supervision)
- [License](#license)

---

## The Problem

University students often struggle to efficiently extract information from large volumes of lecture slides, PDFs, and course materials. Traditional study methods are time-consuming, and getting timely help outside of office hours is difficult. Instructors lack tools to make their uploaded content interactive without writing custom code.

## The Solution

DocMind provides an AI-powered platform where:

- **Students** upload documents and have natural conversations with their content, or chat with AI tutors tailored to their enrolled subjects.
- **Instructors** upload and manage course materials that power AI assistants, monitor bot readiness, and preview the student experience in real time.
- **Admins** oversee platform health, manage users and subjects, and monitor granular analytics and feedback.

---

## Key Features

### For Students
- **Chat with Documents** — Upload PDFs, PPTX, or images and ask questions directly about the content using RAG.
- **AI Subject Tutors** — Get context-aware answers from tutors trained on course-specific materials per semester.
- **Smart Suggestions** — Receive prompt suggestions to guide study sessions.
- **Sequential Chat History** — Chats are auto-named ("Chat 1", "Chat 2", …) and renameable; history is persisted.
- **Feedback System** — Rate AI responses with 👍 / 👎 to continuously improve quality.
- **Upload Resilience** — Retry logic, progress tracking, and elapsed-time indicators for heavy file uploads and LLM calls.

### For Instructors
- **Material Management** — Upload, organize, and delete course materials (PDF, PPTX) per subject and semester.
- **Bot Status Monitoring** — Track whether the AI assistant is live and ready for students.
- **Test Student Bot** — Preview the student-facing chat experience before it goes live (stateless, non-persisted).
- **Semester-Based Organization** — Manage materials across different academic semesters.

### For Admins
- **Dashboard Overview** — Monitor total users, subjects, active chats, and system uptime.
- **User Management** — View, filter, and manage users by role, department, and university ID.
- **Instructor Management** — Assign instructors to subjects and track their activity.
- **Subject Analytics** — Track queries, satisfaction rates, and feedback per subject.
- **Platform Analytics** — Analyze query performance, response times, weekly activity trends, and peak usage hours (charts powered by Recharts).
- **Subject Feedback** — Browse and filter rated AI responses across all subjects.
- **System Access Control** — Toggle student access globally from a dedicated admin panel.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Browser / Client                           │
│   React 19 + Vite + Tailwind CSS + React Router + Framer Motion     │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTPS / REST (Axios)
┌───────────────────────────▼─────────────────────────────────────────┐
│                     FastAPI Backend  (/api)                          │
│  Auth · Subjects · Materials · Chat-Doc · Chat-Tutor · Admin        │
│  Middleware: CORS · RequestID · JWT · Exception Handlers            │
└───────┬───────────────────┬──────────────────┬──────────────────────┘
        │                   │                  │
┌───────▼───────┐  ┌────────▼────────┐  ┌──────▼───────────┐
│  PostgreSQL   │  │   Vector Store  │  │   LLM Provider   │
│  (SQLAlchemy  │  │  pgvector  or   │  │  Gemini / OpenAI │
│  + asyncpg    │  │  Qdrant         │  │  / Cohere        │
│  + Alembic)   │  └─────────────────┘  │  + Ollama local  │
└───────────────┘                        └──────────────────┘
                    ┌──────────────────────────────────────────┐
                    │     RAG Augmentation Layer (optional)    │
                    │  JSON-Planner Agent · source scoping ·   │
                    │       cross-encoder reranking            │
                    └──────────────────────────────────────────┘
```

---

## Tech Stack

| Layer            | Technologies                                                                                        |
|------------------|-----------------------------------------------------------------------------------------------------|
| **Frontend**     | React 19, Vite 7, Tailwind CSS 3, React Router 7, Framer Motion, Recharts, Lucide React, Sonner    |
| **Backend**      | FastAPI 0.110, Uvicorn, SQLAlchemy 2 (async), asyncpg, Alembic, Pydantic v2, python-jose, passlib  |
| **AI / LLM**     | Google Gemini, OpenAI, Cohere, Ollama (local) — provider-agnostic factory pattern                  |
| **Embeddings**   | Gemini, OpenAI, Cohere — swappable via `EMBEDDING_BACKEND` env var                                 |
| **Vector DB**    | pgvector (PostgreSQL extension) · Qdrant — swappable via `VECTOR_DB_BACKEND` env var               |
| **Database**     | PostgreSQL 16 with pgvector extension                                                               |
| **Agent**        | JSON-Planner Agentic RAG (optional, toggleable via `AGENT_ENABLED` env var)                         |
| **Reranking**    | Local cross-encoder via sentence-transformers (optional, `RERANK_ENABLED`) — same factory pattern  |
| **Document Parsing** | PyMuPDF, python-pptx, pypdf — structure-aware chunking (tables + headings)                     |
| **DevOps**       | Docker Compose (Postgres + migration sidecar), Alembic migrations, database seeding                 |

---

## Repository Structure

```
DocMindFull/
├── frontend/                        # React 19 frontend application
│   ├── src/
│   │   ├── assets/                  # Static assets (logo, images)
│   │   │   └── docmind-logo.png
│   │   ├── components/              # Shared UI components
│   │   │   ├── admin/               # Admin-specific components
│   │   │   ├── chat/                # Chat UI components
│   │   │   ├── layout/              # Layout components (sidebar, navbar)
│   │   │   └── ui/                  # Generic UI primitives
│   │   ├── constants/               # App-wide constants
│   │   ├── features/                # Feature flags / grouped logic
│   │   ├── hooks/                   # Custom React hooks
│   │   ├── pages/                   # Page-level components
│   │   │   ├── admin/               # Admin dashboard, analytics, user mgmt
│   │   │   │   ├── AdminDashboard.jsx
│   │   │   │   ├── Analytics.jsx
│   │   │   │   ├── ManageInstructors.jsx
│   │   │   │   ├── ManageSubjects.jsx
│   │   │   │   ├── ManageUsers.jsx
│   │   │   │   ├── SubjectFeedback.jsx
│   │   │   │   └── SystemAccess.jsx
│   │   │   ├── ChatWithDoc.jsx      # Student document chat page
│   │   │   ├── ChatWithTutors.jsx   # Student tutor selection page
│   │   │   ├── TutorChat.jsx        # Student tutor chat page
│   │   │   ├── InstructorHome.jsx   # Instructor dashboard
│   │   │   ├── InstructorSubject.jsx# Instructor material management
│   │   │   ├── UserHome.jsx         # Student home
│   │   │   └── Login.jsx            # Auth page
│   │   ├── routes/                  # React Router route definitions
│   │   ├── services/                # Axios API service layer
│   │   │   ├── apiClient.js         # Base Axios instance + interceptors
│   │   │   ├── authService.js
│   │   │   ├── chatService.js
│   │   │   ├── subjectService.js
│   │   │   ├── adminService.js
│   │   │   ├── uploadService.js
│   │   │   └── systemAccessService.js
│   │   └── utils/                   # Utility helpers
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── backend/
│   ├── docker/
│   │   └── docker-compose.yml       # Postgres 16 + pgvector + migration sidecar
│   ├── docs/                        # Additional backend documentation
│   └── src/
│       ├── main.py                  # FastAPI app entrypoint + lifespan hooks
│       ├── requirements.txt
│       ├── alembic/                 # Database migrations
│       ├── alembic.ini
│       ├── controllers/             # Legacy RAG controller layer
│       │   ├── NLPController.py
│       │   ├── DataController.py
│       │   └── ProcessController.py
│       ├── db/                      # SQLAlchemy engine + ORM models
│       │   ├── session.py
│       │   └── models/              # User, Subject, Semester, Material,
│       │       │                    # Conversation, Message, Feedback, Activity …
│       │       └── (14 model files)
│       ├── helpers/                 # Config, errors, middleware
│       ├── models/                  # Pydantic / legacy data models
│       ├── repositories/            # Data-access layer (repository pattern)
│       ├── routes/                  # FastAPI routers
│       │   ├── auth_router.py
│       │   ├── subjects_router.py
│       │   ├── materials_router.py
│       │   ├── chat_doc_router.py
│       │   ├── chat_tutor_router.py
│       │   ├── chat_feedback_router.py
│       │   ├── admin_router.py
│       │   ├── system_access_router.py
│       │   └── health.py
│       ├── schemas/                 # Pydantic request/response schemas
│       ├── scripts/                 # Maintenance scripts (e.g. reindex_materials)
│       ├── seeds/                   # Initial data seeder
│       ├── services/                # Business-logic service layer
│       │   ├── auth_service.py
│       │   ├── document_chat_service.py
│       │   ├── tutor_chat_service.py
│       │   ├── ingestion_service.py
│       │   ├── rag_service.py
│       │   ├── material_service.py
│       │   ├── subject_service.py
│       │   ├── admin_stats_service.py
│       │   ├── admin_users_service.py
│       │   ├── feedback_service.py
│       │   └── file_service.py
│       └── stores/                  # Provider-agnostic integrations
│           ├── llm/                 # Gemini · OpenAI · Cohere providers
│           ├── vectordb/            # pgvector · Qdrant providers
│           ├── agent/               # JSON-Planner agentic RAG strategy
│           └── rerank/              # Cross-encoder reranker (optional)
│
└── README.md
```

---

## API Overview

The backend exposes a fully documented REST API. Key route groups:

| Prefix | Description |
|--------|-------------|
| `GET /health` | Health check |
| `POST /api/auth/login` · `POST /api/auth/logout` | JWT authentication |
| `GET /api/subjects` · `POST /api/admin/subjects` | Subject management |
| `GET /api/semesters` | Semester listing |
| `POST /api/subjects/{id}/materials` | Upload course material |
| `DELETE /api/materials/{id}` | Remove a material |
| `POST /api/chats/documents` · `POST /api/chats/documents/{id}/messages` | Document chat |
| `POST /api/chats/tutor` · `POST /api/chats/tutor/{id}/messages` | Tutor chat |
| `POST /api/chats/{id}/messages/{msg_id}/feedback` | Rate a message |
| `GET /api/admin/users` · `GET /api/admin/stats` | Admin user & platform stats |
| `GET /api/admin/analytics` · `GET /api/admin/activity` | Analytics & activity log |
| `POST /api/system/access` | Toggle global student access |

> The full API specification is documented in [`frontend/API_SPECIFICATION.md`](frontend/API_SPECIFICATION.md).

---

## Getting Started

### Prerequisites

| Tool | Version |
|------|---------|
| Node.js | ≥ 20 |
| Python | ≥ 3.10 |
| Docker & Docker Compose | Any recent version |
| PostgreSQL | 16 (via Docker recommended) |

---

### Backend Setup

**1. Start PostgreSQL with pgvector via Docker:**

```bash
cd backend/docker
cp .env.example .env          # fill in POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT
docker compose up -d postgres
```

**2. Apply migrations and seed initial data:**

```bash
docker compose run --rm migrate
```

**3. Configure environment:**

```bash
cd backend/src
cp .env.example .env          # fill in all required values (see Environment Variables below)
```

**4. Install dependencies and start the server:**

```bash
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

---

### Frontend Setup

```bash
cd frontend
cp .env.example .env          # set VITE_API_BASE_URL=http://localhost:8000
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`.

---

## Environment Variables

### Backend (`backend/src/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | — |
| `GENERATION_BACKEND` | LLM provider: `GEMINI`, `OPENAI`, `COHERE` | `GEMINI` |
| `EMBEDDING_BACKEND` | Embedding provider: `GEMINI`, `OPENAI`, `COHERE` | `GEMINI` |
| `GENERATION_MODEL_ID` | Model ID for text generation | — |
| `EMBEDDING_MODEL_ID` | Model ID for embeddings | — |
| `EMBEDDING_SIZE` | Embedding vector dimension | `768` |
| `GEMINI_API_KEY` | Google Gemini API key | — |
| `OPENAI_API_KEY` | OpenAI API key | — |
| `COHERE_API_KEY` | Cohere API key | — |
| `VECTOR_DB_BACKEND` | Vector store: `PGVECTOR`, `QDRANT` | `PGVECTOR` |
| `AGENT_ENABLED` | Enable agentic RAG (JSON-Planner) | `false` |
| `AGENT_STRATEGY` | Agent strategy name | `JSON_PLANNER` |
| `AGENT_SOURCE_FILTER_ENABLED` | Let the planner scope retrieval to named materials (re-index first) | `false` |
| `RERANK_ENABLED` | Enable cross-encoder reranking of retrieved chunks | `false` |
| `RERANK_BACKEND` | Reranker backend: `LOCAL_CROSS_ENCODER` | — |
| `RERANK_MODEL_ID` | Cross-encoder model, e.g. `BAAI/bge-reranker-base` | — |
| `RERANK_DEVICE` | Torch device: `cuda`, `cpu`, or unset (auto) | — |
| `RERANK_OVERFETCH` | Candidate multiplier for over-fetch (`limit × N`) | `3` |
| `RERANK_TOP_N` | Final cap on reranked chunks (defaults to caller `limit`) | — |
| `JWT_SECRET` | JWT signing secret (32+ bytes) | — |
| `JWT_EXPIRE_MINUTES` | Token lifetime | `720` |
| `CORS_ORIGINS` | Allowed frontend origins | `["http://localhost:5173"]` |
| `STUDENT_ACCESS_DEFAULT_ENABLED` | Initial student access toggle state | `true` |
| `UPLOAD_MATERIAL_MAX_MB` | Max upload size for materials | `50` |
| `UPLOAD_DOC_MAX_MB` | Max upload size for document chats | `25` |
| `UPLOAD_DOC_MAX_FILES` | Max files per document chat | `5` |

---

## User Roles

| Role | Description |
|------|-------------|
| **Student** | Chats with uploaded documents and AI tutors for enrolled subjects |
| **Instructor** | Manages course materials per subject/semester, monitors bot status, tests the student experience |
| **Admin** | Oversees the entire platform — manages users, subjects, instructors, views analytics and feedback |

---

## Data Model

The database is managed by **Alembic** migrations and includes the following core entities:

| Entity | Description |
|--------|-------------|
| `User` | Platform users (Student, Instructor, Admin roles) with faculty/department |
| `Subject` | Courses, linked to semesters and instructors via junction tables |
| `Semester` | Academic terms (e.g., Fall 2024, Spring 2025) |
| `Material` | Course files uploaded by instructors; ingested into the vector store |
| `Conversation` | Chat sessions (document-based or tutor-based) |
| `Message` | Individual chat turns (user + assistant) |
| `DocumentFile` | Files attached to a document-chat session |
| `Feedback` | Thumbs up/down ratings on individual assistant messages |
| `Activity` | Admin activity log |
| `SystemFlag` | Platform-wide toggles (e.g., student access lock) |
| `TokenBlocklist` | Revoked JWT tokens |
| `DataChunk` / `Asset` | Legacy RAG pipeline entities |

---

## AI / RAG Pipeline

DocMind implements a **Retrieval-Augmented Generation (RAG)** pipeline with the following stages:

```
Document Upload
      │
      ▼
 Ingestion Service  (structure-aware chunking)
  ├─ Parse PDF/PPTX → text (PyMuPDF, python-pptx, pypdf)
  ├─ Extract tables  → kept intact as atomic Markdown chunks
  ├─ Detect headings → prepended as breadcrumbs + stored on each chunk
  ├─ Split prose     → paragraph → line → sentence aware (with overlap)
  └─ Embed chunks    → vector embeddings (Gemini / OpenAI / Cohere)
                            │  (each chunk stamped with material_id,
                            ▼   material_name, section, page/slide)
                    Vector Store (pgvector / Qdrant)

User Question
      │
      ▼
 [Optional] JSON-Planner Agent  ─── decides whether to retrieve, and may
      │                              scope the search to named materials
      ▼
 RAG Service
  ├─ Embed question
  ├─ Similarity search in vector store (optionally scoped by material_id)
  ├─ [Optional] Cross-encoder rerank — over-fetch by recall, keep best by precision
  ├─ Build prompt with retrieved, source-attributed context
  └─ Stream/return cited LLM response (Gemini / OpenAI / Cohere)
```

**Structure-aware chunking** — Ingestion preserves document structure for better retrieval: tables are detected natively and emitted as intact Markdown chunks (never sliced into garbled text), section headings are detected by font size and prepended to each chunk as breadcrumbs, and prose is split on paragraph → line → sentence boundaries with overlap instead of hard character slicing. Every chunk is stamped with its owning `material_id`/`material_name`, `section`, and `page`/`slide`.

**Source-attributed answers** — Retrieved context is rendered with its source filename, section, and page, and the model is instructed to cite the source of each fact it states (e.g. `(Lecture03.pdf, Third Normal Form)`).

**Provider Switching** — All LLM, embedding, vector-store, and reranker integrations follow the same factory pattern. Switching providers requires only changing an environment variable; no application code changes needed.

**Agentic RAG (optional)** — When `AGENT_ENABLED=true`, the JSON-Planner agent evaluates each user turn and decides whether retrieval is necessary before calling the LLM, reducing unnecessary API calls and improving response quality. The planner is given a manifest of the subject's indexed materials.

**Source-scoped retrieval (optional, off by default)** — When `AGENT_SOURCE_FILTER_ENABLED=true`, the planner may scope retrieval to the specific materials a question is about (validated against the subject's material allowlist), with a one-shot fallback to the whole subject if the scoped search finds nothing. Requires chunks stamped with `material_id` — re-index legacy materials first with `python -m scripts.reindex_materials`.

**Cross-encoder reranking (optional, off by default)** — When `RERANK_ENABLED=true`, similarity search over-fetches `limit × RERANK_OVERFETCH` candidates (recall) and a cross-encoder truncates back to the best `limit` (precision), so the generation model gets fewer, cleaner chunks. The `LOCAL_CROSS_ENCODER` backend uses `sentence-transformers` (kept out of `requirements.txt`; install with `pip install sentence-transformers`). Reranker faults soft-degrade to vector order — they never error a chat turn.

---

## Academic Context

DocMind is designed around the university academic structure:

- **Faculties** — Engineering, Science, Medicine, Pharmacy
- **Departments** — Computer Science, Software Engineering, Data Science, and more
- **Semesters** — Organized by academic terms (e.g., Fall 2024, Spring 2025)
- **Subjects** — Data Structures, Algorithms, Web Development, AI, Database Management, Cloud Computing

---

## Getting Started (Quick Summary)

```bash
# 1. Start DB
cd backend/docker && docker compose up -d postgres && docker compose run --rm migrate

# 2. Start backend
cd backend/src && pip install -r requirements.txt && uvicorn main:app --reload

# 3. Start frontend
cd frontend && npm install && npm run dev
```

---

## Team

*Graduation Project — 2025/2026*

### Frontend
| Name | GitHub |
|-----|------|
| **Abdulrhman Mohamed** | https://github.com/yeagx |
| **Mohamed Amgad** | https://github.com/Mohamedamged17 |
| **Youssef Kamal** | https://github.com/MajikorX |

### Backend
| Name | GitHub |
|-----|------|
| **Mohamed Younes** | https://github.com/mohamedAY2004 |

### Mobile
| Name | GitHub |
|-----|------|
| **Ahmed Abo El-Naga** | https://github.com/AhmedAboelnaga004 |

### AI
| Name | GitHub |
|-----|------|
| **Amr Mustafa** | https://github.com/AmrMustafa2 |
| **Mohamed Younes** | https://github.com/mohamedAY2004 |
| **Ahmed Abo El-Naga** | https://github.com/AhmedAboelnaga004 |

### RAG Evaluation
| Name | GitHub |
|-----|------|
| **Amr Mustafa** | https://github.com/AmrMustafa2 |
| **Youssef Kamal** | https://github.com/MajikorX |
---

## Academic Supervision

This project was developed under the supervision of:

| Name | GitHub |
|-----|------|
| **Dr. Ahmed Said** | https://github.com/dr-ahmed-said |

---

## License

This project is developed as part of an academic graduation project. See [`backend/LICENSE`](backend/LICENSE) for details.
