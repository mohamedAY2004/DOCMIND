# DocMindFull

DocMindFull is an AI-powered academic assistant platform that helps students learn from course materials through conversational AI, while giving instructors and administrators operational control over subjects, users, and engagement analytics.

## Project Purpose

The project is designed to solve three core problems in modern academic workflows:

- Students need a faster way to understand dense learning materials.
- Instructors need better tooling to organize content and monitor usage.
- Admins need visibility into system activity, adoption, and feedback.

DocMindFull addresses these needs with a role-based full-stack application that combines document-aware chat, subject tutors, and operational dashboards.

## What This Project Is

This repository contains a full-stack monorepo with:

- A React frontend for students, instructors, and admins.
- A FastAPI backend with authentication, subject/material management, and AI chat APIs.
- PostgreSQL + pgvector infrastructure for persistence and vector-based retrieval.

## Core Capabilities

- **Document Chat**: Students can upload files and ask questions about the content.
- **Tutor Chat**: Subject-specific AI tutoring experience.
- **Instructor Workspace**: Manage subjects and educational materials.
- **Admin Console**: User management, subject insights, feedback review, and analytics.
- **Role-Based Access Control**: Dedicated flows for `student`, `instructor`, and `admin`.

## High-Level Architecture

- **Frontend**: React + Vite + Tailwind CSS (`frontend/`)
- **Backend**: FastAPI + SQLAlchemy + Alembic (`backend/src/`)
- **Database**: PostgreSQL with `pgvector` extension (`backend/docker/docker-compose.yml`)
- **AI Layer**: Pluggable LLM providers and vector DB integrations in `backend/src/stores/`

## Repository Structure

```text
DocMindFull/
├── frontend/                 # React application (UI, routes, services)
├── backend/
│   ├── src/                  # FastAPI source code
│   ├── docker/               # Local infrastructure (PostgreSQL/pgvector)
│   └── README.md             # Backend-specific setup notes
└── README.md                 # You are here
```

## Quick Start

### 1) Frontend

```bash
cd frontend
npm install
npm run dev
```

By default, Vite serves the app on `http://localhost:5173`.

### 2) Backend

```bash
cd backend/src
pip install -r requirements.txt
```

Run local infrastructure from `backend/docker`:

```bash
docker compose up -d
```

Then start the API server from `backend/src`:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

> For backend environment setup details, see `backend/README.md`.

## Technology Stack

- **Frontend**: React, Vite, Tailwind CSS, React Router, Axios
- **Backend**: FastAPI, Uvicorn, SQLAlchemy (async), Alembic, asyncpg
- **AI/ML**: LangChain, OpenAI, Google GenAI, Cohere
- **Storage/Retrieval**: PostgreSQL, pgvector, Qdrant client support

## API Surface (Overview)

The backend exposes:

- Health endpoint(s) for service monitoring.
- `/api` routes for auth, subjects, materials, chat, feedback, and admin analytics.
- Legacy internal debug routes under `/api/v1/*` for development workflows.

## Development Notes

- Keep frontend and backend environment variables in their respective `.env` files.
- Apply database schema updates with Alembic before running new backend changes.
- Review existing architecture conventions before introducing new modules.

## Contributors

> Fill this section with your contributors.

- `Your Name` — `Role` — `GitHub/Contact`
- `Contributor Name` — `Role` — `GitHub/Contact`
- `Contributor Name` — `Role` — `GitHub/Contact`

## License

No license is currently declared in this repository. Add a license before public distribution.
