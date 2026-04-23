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
    ) -> None:
        self._vectordb = vectordb_client
        self._embedding = embedding_client
        self._generation = generation_client
        self._templates = template_parser

    async def index_chunks(
        self,
        collection_name: str,
        chunks: List[IngestedChunk],
        do_reset: bool = False,
        id_prefix: Optional[str] = None,
    ) -> int:
        if not chunks:
            return 0
        texts = [c.text for c in chunks]
        metas = [c.metadata for c in chunks]
        vectors = [
            self._embedding.embed_text(text=t, document_type=DocumentTypeEnum.DOCUMENT.value)[0]
            for t in texts
        ]
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

    async def delete_collection(self, collection_name: str) -> None:
        await self._vectordb.delete_collection(collection_name=collection_name)

    async def search(
        self,
        collection_name: str,
        query: str,
        *,
        limit: int = 5,
        threshold: float = 0.5,
    ) -> list:
        vector = self._embedding.embed_text(
            text=query, document_type=DocumentTypeEnum.QUERY.value
        )
        if not vector:
            logger.error("Failed to embed query for collection %s", collection_name)
            return []
        vector = vector[0]
        results = await self._vectordb.search_by_vector(
            collection_name=collection_name,
            vector=vector,
            limit=limit,
            threshold=threshold,
        )
        return results or []

    async def answer(
        self,
        collection_name: str,
        query: str,
        *,
        limit: int = 5,
        threshold: float = 0.5,
        history: Optional[list[dict]] = None,
        subject_name: str = "",
    ) -> str:
        retrieved = await self.search(
            collection_name, query, limit=limit, threshold=threshold
        )
        if not retrieved:
            return (
                "I could not find any relevant information in the indexed materials "
                "to answer this question."
            )

        system_prompt = self._templates.get(
            group="rag", key="system_prompt",
            variables={"subject_name": subject_name},
        )
        docs_block = "\n".join(
            self._templates.get(
                group="rag",
                key="document_prompt",
                variables={"doc_num": i + 1, "chunk_text": chunk.chunk_text},
            )
            for i, chunk in enumerate(retrieved)
        )
        footer = self._templates.get(group="rag", key="footer_prompt")

        chat_history = [
            self._generation.construct_prompt(
                prompt=system_prompt, role=self._generation.enums.SYSTEM.value
            )
        ]
        if history:
            chat_history.extend(history)

        full_prompt = "\n\n".join([docs_block, footer, query])
        reply = self._generation.generate_text(prompt=full_prompt, chat_history=chat_history)
        return reply or ""
