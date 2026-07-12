"""Deterministic in-memory fakes for the LLM, embedding, and vector-store
providers so the integration tests never touch the network or a real vector DB.

The agent layer is disabled in tests (``app.state.agent_client = None``), so the
chat services exercise the classic RAG path through these fakes.
"""
from __future__ import annotations

import hashlib
from enum import Enum
from typing import List, Union

from models.db_schemes import RetrievedChunk
from stores.llm.LLMInterface import LLMInterface
from stores.rerank.RerankInterface import RerankInterface
from stores.vectordb.VectorDBInterface import VectorDBInterface

# Small fixed embedding dimension — the fake vector store ignores the real
# dimensionality, so any consistent size works.
FAKE_EMBED_DIM = 8

# Canned generation output. Tests assert this is what comes back from chat /
# test-bot so they stay deterministic.
FAKE_REPLY = "This is a deterministic fake LLM reply."


class _Roles(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


def _vector_for(text: str) -> List[float]:
    """Map text → a stable pseudo-random unit-ish vector (deterministic)."""
    digest = hashlib.sha256((text or "").encode("utf-8")).digest()
    return [(digest[i] / 255.0) for i in range(FAKE_EMBED_DIM)]


class FakeLLM(LLMInterface):
    """Implements both the generation and embedding sides of ``LLMInterface``."""

    def __init__(self) -> None:
        self.embedding_size = FAKE_EMBED_DIM
        self.enums = _Roles

    def set_generation_model(self, model_id: str) -> None:  # noqa: D401
        return None

    def set_embedding_model(self, model_id: str, embedding_size: int) -> None:
        if embedding_size:
            self.embedding_size = embedding_size

    def generate_text(
        self,
        prompt: str,
        chat_history: list = [],
        generation_max_tokens: int = None,
        temperature: float = None,
    ):
        return FAKE_REPLY

    def embed_text(self, text: Union[str, List[str]], document_type: str = None):
        items = [text] if isinstance(text, str) else list(text)
        return [_vector_for(t) for t in items]

    def construct_prompt(self, prompt: str, role: str):
        return {"role": role, "content": prompt}


class FakeVectorDB(VectorDBInterface):
    """In-memory vector store: ``{collection: {record_id: (text, vector, meta)}}``."""

    def __init__(self) -> None:
        self.collections: dict[str, dict] = {}

    async def connect(self):
        return None

    async def disconnect(self):
        return None

    async def is_collection_exists(self, collection_name: str) -> bool:
        return collection_name in self.collections

    async def list_all_collections(self) -> List:
        return list(self.collections.keys())

    async def get_collection_info(self, collection_name: str) -> dict:
        return {"name": collection_name, "count": len(self.collections.get(collection_name, {}))}

    async def delete_collection(self, collection_name: str):
        self.collections.pop(collection_name, None)

    async def create_collection(
        self, collection_name: str, embedding_size: int, do_reset: bool = False
    ):
        if do_reset or collection_name not in self.collections:
            self.collections[collection_name] = {}

    async def insert_one(
        self, collection_name: str, text: str, vector: list,
        metadata: dict = None, record_id: str = None,
    ):
        self.collections.setdefault(collection_name, {})
        rid = record_id or str(len(self.collections[collection_name]))
        self.collections[collection_name][rid] = (text, vector, metadata or {})

    async def insert_many(
        self, collection_name: str, texts: list, vectors: list,
        metadata: list = None, record_ids: list = None, batch_size: int = 50,
    ):
        self.collections.setdefault(collection_name, {})
        metas = metadata or [{} for _ in texts]
        ids = record_ids or [str(i) for i in range(len(texts))]
        for text, vec, meta, rid in zip(texts, vectors, metas, ids):
            self.collections[collection_name][rid] = (text, vec, meta or {})

    async def delete_by_material_id(self, collection_name: str, material_id: str) -> bool:
        store = self.collections.get(collection_name)
        if store is None:
            return False
        stale = [
            rid for rid, (_, _, meta) in store.items()
            if (meta or {}).get("material_id") == material_id
        ]
        for rid in stale:
            del store[rid]
        return True

    async def search_by_vector(
        self, collection_name: str, vector: list, limit: int, threshold: float,
        material_ids: list | None = None, with_vectors: bool = False,
    ) -> List[RetrievedChunk]:
        store = self.collections.get(collection_name)
        if not store:
            return []
        # Simple dot-product ranking; return everything (clamped to ``limit``) so
        # chat/test-bot have context to answer with. Score is not thresholded
        # strictly here — the fake always surfaces indexed chunks.
        scored = []
        for text, vec, meta in store.values():
            if material_ids and (meta or {}).get("material_id") not in material_ids:
                continue
            score = float(sum(a * b for a, b in zip(vector, vec)))
            scored.append(RetrievedChunk(
                chunk_text=text, score=score, chunk_metadata=meta or {},
                embedding=list(vec) if with_vectors else None,
            ))
        scored.sort(key=lambda c: c.score, reverse=True)
        return scored[:limit]


class FakeReranker(RerankInterface):
    """Deterministic reranker for tests.

    Scores candidates by an optional ``score_map`` keyed on ``chunk_text``
    (higher = more relevant); unmapped chunks fall back to query-substring
    overlap so ordering is assertable without a real model. Set ``raises=True``
    to exercise the ``RAGService`` soft-degrade path. ``last_top_n`` records the
    ``top_n`` it was last asked for.
    """

    def __init__(self, score_map: dict | None = None, raises: bool = False) -> None:
        self.score_map = score_map or {}
        self.raises = raises
        self.last_top_n: int | None = None

    async def rerank(self, query: str, candidates: list, *, top_n: int) -> list:
        self.last_top_n = top_n
        if self.raises:
            raise RuntimeError("boom")
        if not candidates:
            return []

        def _score(chunk) -> float:
            text = getattr(chunk, "chunk_text", "") or ""
            if text in self.score_map:
                return float(self.score_map[text])
            return float(1 if query and query.lower() in text.lower() else 0)

        ranked = sorted(candidates, key=_score, reverse=True)
        return ranked[:top_n]
