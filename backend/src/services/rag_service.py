"""Retrieval-augmented generation utilities.

Wraps the existing ``LLMProviderFactory`` / ``VectorDBProviderFactory`` stores
behind a simple, typed interface consumed by material indexing, document chat,
and tutor chat.
"""
from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from stores.llm.LLMEnums import DocumentTypeEnum

from services.ingestion_service import IngestedChunk

logger = logging.getLogger("docmind.rag")


def _citation_vars(chunk) -> dict:
    """Pull citable provenance off a retrieved chunk for ``document_prompt``.

    Chunks carry the metadata stamped at ingestion (``source``, ``section``,
    ``page``/``slide``). We expose it to the model so it can attribute claims;
    missing keys (e.g. ``page`` on a PPTX/txt chunk) degrade to a dash.
    """
    meta = getattr(chunk, "chunk_metadata", None) or {}
    page = meta.get("page") or meta.get("slide")
    # Prefer the human-readable material name (stamped at index time) over the
    # randomised storage filename in ``source``.
    return {
        "chunk_text": getattr(chunk, "chunk_text", "") or "",
        "source": meta.get("material_name") or meta.get("source") or "unknown",
        "section": meta.get("section") or "-",
        "page": page if page is not None else "-",
    }


def collection_for_subject(subject_id: str) -> str:
    """Stable collection name for a subject's tutor-chat corpus."""
    return f"tutor_{subject_id}".lower()


def collection_for_conversation(conv_id: str) -> str:
    """Stable collection name for a single doc-chat conversation."""
    return f"doc_{conv_id}".lower()


class RAGService:
    """Index / search / answer over a named collection.

    The ``llm``, ``embedding`` and ``vectordb`` clients are created by the
    factories at startup and stored on ``app.state``; routes / services pass
    them into this class so it remains unit-test-friendly.
    """

    def __init__(
        self,
        *,
        vectordb_client,
        embedding_client,
        generation_client,
        template_parser,
        rerank_client=None,
        rerank_overfetch: int = 3,
        rerank_top_n: Optional[int] = None,
    ) -> None:
        self._vectordb = vectordb_client
        self._embedding = embedding_client
        self._generation = generation_client
        self._templates = template_parser
        # Optional cross-encoder reranker. When None the retrieval path is
        # byte-identical to before (no over-fetch, no reorder).
        self._rerank = rerank_client
        self._rerank_overfetch = max(1, rerank_overfetch)
        self._rerank_top_n = rerank_top_n

    async def index_chunks(
        self,
        collection_name: str,
        chunks: List[IngestedChunk],
        do_reset: bool = False,
        id_prefix: Optional[str] = None,
        material_name: Optional[str] = None,
    ) -> int:
        if not chunks:
            return 0
        texts = [c.text for c in chunks]
        # Stamp a stable owning-material identity onto every chunk so retrieval
        # can be scoped to specific materials later (Phase 2 source filtering)
        # and citations can show the human-readable name. ``id_prefix`` is the
        # material/file id the caller already passes for record-id uniqueness.
        stamp: dict = {}
        if id_prefix is not None:
            stamp["material_id"] = id_prefix
        if material_name is not None:
            stamp["material_name"] = material_name
        metas = [{**c.metadata, **stamp} for c in chunks]
        vectors = []
        for t in texts:
            result = await self._embedding.embed_text_async(
                text=t, document_type=DocumentTypeEnum.DOCUMENT.value
            )
            vectors.append(result[0])
        # IDs must be globally unique within the collection so that indexing a
        # new material never overwrites a previously indexed one. We combine an
        # optional caller-supplied prefix (e.g. the material id) with a random
        # UUID per chunk.
        prefix = (id_prefix or uuid.uuid4().hex).replace("-", "")
        record_ids = [f"{collection_name}_{prefix}_{i}" for i in range(len(texts))]
        await self._vectordb.create_collection(
            collection_name=collection_name,
            embedding_size=self._embedding.embedding_size,
            do_reset=do_reset,
        )
        await self._vectordb.insert_many(
            collection_name=collection_name,
            texts=texts,
            vectors=vectors,
            metadata=metas,
            record_ids=record_ids,
        )
        return len(chunks)

    # ------------------------------------------------------------------ #
    # Prompt building (shared by the non-agent path and the agent's
    # synthesis step so both produce identically-shaped, citable context).
    # ------------------------------------------------------------------ #
    def build_system_prompt(self, subject_name: str, subject_manifest: str = "") -> str:
        return self._templates.get(
            group="rag",
            key="system_prompt",
            variables={
                "subject_name": subject_name,
                "subject_manifest": subject_manifest,
            },
        )

    def build_docs_block(self, retrieved: list) -> str:
        """Render retrieved chunks into a numbered, source-attributed block."""
        return "\n".join(
            self._templates.get(
                group="rag",
                key="document_prompt",
                variables={"doc_num": i + 1, **_citation_vars(chunk)},
            )
            for i, chunk in enumerate(retrieved)
        )

    async def delete_collection(self, collection_name: str) -> None:
        await self._vectordb.delete_collection(collection_name=collection_name)

    async def delete_material(self, collection_name: str, material_id: str) -> None:
        """Evict every chunk owned by one material/file from a collection.

        Must be called whenever a material or doc-chat file is deleted;
        otherwise its chunks stay searchable and chat keeps citing them.
        """
        await self._vectordb.delete_by_material_id(
            collection_name=collection_name, material_id=material_id
        )

    async def search(
        self,
        collection_name: str,
        query: str,
        *,
        limit: int = 5,
        threshold: float = 0.5,
        material_ids: Optional[List[str]] = None,
    ) -> list:
        vector = await self._embedding.embed_text_async(
            text=query, document_type=DocumentTypeEnum.QUERY.value
        )
        if not vector:
            # Intentional soft-degrade: on an embedding failure we return no
            # context so chat answers "no relevant info" rather than erroring.
            logger.error("Failed to embed query for collection %s", collection_name)
            return []
        vector = vector[0]

        if self._rerank is None:
            results = await self._vectordb.search_by_vector(
                collection_name=collection_name,
                vector=vector,
                limit=limit,
                threshold=threshold,
                material_ids=material_ids or None,
            )
            return results or []

        # Rerank path: over-fetch by recall, then truncate by precision so the
        # generation model gets fewer, cleaner chunks within the same budget.
        keep = self._rerank_top_n or limit
        candidates = await self._vectordb.search_by_vector(
            collection_name=collection_name,
            vector=vector,
            limit=keep * self._rerank_overfetch,
            threshold=threshold,
            material_ids=material_ids or None,
        )
        candidates = candidates or []
        if not candidates:
            return []
        try:
            reranked = await self._rerank.rerank(query, candidates, top_n=keep)
        except Exception:  # noqa: BLE001 - never let a reranker fault 500 a turn
            logger.exception(
                "Reranker failed for collection %s; falling back to vector order",
                collection_name,
            )
            return candidates[:keep]
        # Empty rerank output also degrades to the vector ordering.
        return reranked or candidates[:keep]

    async def answer(
        self,
        collection_name: str,
        query: str,
        *,
        limit: int = 5,
        threshold: float = 0.5,
        history: Optional[list[dict]] = None,
        subject_name: str = "",
        subject_manifest: str = "",
    ) -> str:
        retrieved = await self.search(
            collection_name, query, limit=limit, threshold=threshold
        )
        if not retrieved:
            return (
                "I could not find any relevant information in the indexed materials "
                "to answer this question."
            )

        system_prompt = self.build_system_prompt(subject_name, subject_manifest)
        docs_block = self.build_docs_block(retrieved)
        footer = self._templates.get(group="rag", key="footer_prompt")

        chat_history = [
            self._generation.construct_prompt(
                prompt=system_prompt, role=self._generation.enums.SYSTEM.value
            )
        ]
        if history:
            chat_history.extend(history)

        full_prompt = "\n\n".join([docs_block, footer, query])
        reply = await self._generation.generate_text_async(prompt=full_prompt, chat_history=chat_history)
        return reply or ""
