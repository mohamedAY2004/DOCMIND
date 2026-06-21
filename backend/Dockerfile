# DocMind backend API image.
#
# Build context is `backend/` (so we can reach both `src/` and, if needed,
# the docker assets). The app code lives in `src/` and is run with uvicorn.
#
# Python is pinned to 3.10 to match the project's `mini-rag` conda env; the
# heavy deps (PyMuPDF, asyncpg, bcrypt, numpy, qdrant-client, ...) all ship
# manylinux wheels for cp310, so no compiler toolchain is required at runtime.

FROM python:3.10-slim AS base

# ---- Python / pip hygiene -------------------------------------------------
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ---- OS deps --------------------------------------------------------------
# - libgl1 / libglib2.0-0: required by PyMuPDF at import time on slim images.
# - curl: used by the HEALTHCHECK below.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/src

# ---- Python deps (cached layer) ------------------------------------------
# Copy only requirements first so changes to source don't bust the pip cache.
COPY src/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ---- Application code -----------------------------------------------------
COPY src/ ./

# Local storage used by the legacy RAG controllers (uploads + on-disk index).
# Mount a volume here in production so data survives container restarts.
RUN mkdir -p assets/files assets/database

# ---- Runtime --------------------------------------------------------------
# Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Schema is owned by Alembic and applied by the `migrate` sidecar in
# docker-compose, so the API container only serves traffic.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
