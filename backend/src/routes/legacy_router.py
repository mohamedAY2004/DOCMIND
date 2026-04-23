"""Internal RAG-debug routes (``/api/v1/data/*`` and ``/api/v1/nlp/*``).

These are **not** part of the DocMind public API (spec §4–§10). They are kept
so the RAG pipeline can be poked at directly during development. Tagged as
``internal``/``legacy`` so they render separately in the OpenAPI schema.
"""
from __future__ import annotations

from fastapi import APIRouter

from . import base, data, nlp

legacy_router = APIRouter(tags=["internal", "legacy"])

legacy_router.include_router(base.base_router)
legacy_router.include_router(data.data_router)
legacy_router.include_router(nlp.nlp_router)
