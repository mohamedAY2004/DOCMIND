"""Backfill chunk metadata by re-indexing every processed material.

Phase 2 source-scoped retrieval filters on ``metadata.material_id`` (and shows
``metadata.material_name`` in citations), both of which are stamped onto chunks
at index time by :meth:`RAGService.index_chunks`. Materials indexed *before*
that change don't carry those keys, so a filtered search would never match
them. Run this once to rebuild each subject's collection from the files still
on disk, after which ``AGENT_SOURCE_FILTER_ENABLED=true`` is safe.

Usage (from ``backend/src`` with the ``mini-rag`` env active)::

    python -m scripts.reindex_materials            # all subjects
    python -m scripts.reindex_materials SUBJECT_ID # one subject
    python -m scripts.reindex_materials --dry-run  # report, don't write

Each subject's collection is reset on the first material so the rebuild is
clean (no orphan chunks from a previous run with a different chunk count).
Re-ingestion is derived entirely from ``storage_path``; no embeddings are
read back, so this is idempotent.
"""
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

from sqlalchemy import select

from db.models import Material, MaterialStatus
from db.session import create_engine_and_sessionmaker
from helpers.config import get_settings
from services.ingestion_service import ingest_file
from services.rag_service import RAGService, collection_for_subject
from stores.llm import LLMProviderFactory
from stores.vectordb import VectorDBProviderFactory

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("docmind.reindex")


async def _processed_materials(session, subject_id: str | None):
    stmt = select(Material).where(Material.status == MaterialStatus.PROCESSED)
    if subject_id:
        stmt = stmt.where(Material.subject_id == subject_id)
    stmt = stmt.order_by(Material.subject_id, Material.created_at.asc())
    return (await session.execute(stmt)).scalars().all()


async def reindex(subject_id: str | None = None, *, dry_run: bool = False) -> None:
    settings = get_settings()

    embedding_client = LLMProviderFactory(settings).create(settings.EMBEDDING_BACKEND)
    embedding_client.set_embedding_model(
        settings.EMBEDDING_MODEL_ID, settings.EMBEDDING_SIZE
    )
    vectordb_client = VectorDBProviderFactory(settings).create(
        provider=settings.VECTOR_DB_BACKEND
    )
    await vectordb_client.connect()

    # generation/templates are unused on the indexing path.
    rag = RAGService(
        vectordb_client=vectordb_client,
        embedding_client=embedding_client,
        generation_client=None,
        template_parser=None,
    )

    engine, session_maker = create_engine_and_sessionmaker(settings.DATABASE_URL)
    try:
        async with session_maker() as session:
            materials = await _processed_materials(session, subject_id)

        if not materials:
            logger.info("No processed materials found%s.",
                        f" for subject {subject_id}" if subject_id else "")
            return

        reset_done: set[str] = set()
        total_chunks = 0
        for m in materials:
            path = Path(m.storage_path)
            if not path.exists():
                logger.warning("SKIP %s (%s): file missing at %s",
                               m.id, m.name, m.storage_path)
                continue

            first_for_subject = m.subject_id not in reset_done
            reset_done.add(m.subject_id)

            chunks = await asyncio.to_thread(ingest_file, path)
            logger.info("%s %s (%s): %d chunks%s",
                        "DRY-RUN" if dry_run else "INDEX",
                        m.id, m.name, len(chunks),
                        " [reset collection]" if first_for_subject else "")
            if dry_run or not chunks:
                continue

            count = await rag.index_chunks(
                collection_name=collection_for_subject(m.subject_id),
                chunks=chunks,
                do_reset=first_for_subject,
                id_prefix=m.id,
                material_name=m.name,
            )
            total_chunks += count

        logger.info("Done. Re-indexed %d chunks across %d material(s).",
                    total_chunks, len(materials))
    finally:
        await vectordb_client.disconnect()
        await engine.dispose()


def main() -> None:
    args = [a for a in sys.argv[1:]]
    dry_run = "--dry-run" in args
    positional = [a for a in args if not a.startswith("--")]
    subject_id = positional[0] if positional else None
    asyncio.run(reindex(subject_id, dry_run=dry_run))


if __name__ == "__main__":
    main()
