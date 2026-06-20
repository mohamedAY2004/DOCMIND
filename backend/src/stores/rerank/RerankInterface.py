"""Abstract reranker interface.

A reranker reorders a set of already-retrieved candidate chunks by their
relevance to the query and returns the best ``top_n``. It sits between the
vector search and prompt synthesis inside ``RAGService.search`` so the small
generation model receives fewer, higher-precision chunks.

The interface is deliberately thin so alternative backends (a local
cross-encoder today, a managed rerank API later) can slot in without touching
callers, mirroring ``stores/agent/AgentInterface.py``.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class RerankInterface(ABC):
    """Contract every rerank backend must honour."""

    @abstractmethod
    async def rerank(self, query: str, candidates: List, *, top_n: int) -> List:
        """Return the ``top_n`` ``candidates`` most relevant to ``query``.

        ``candidates`` are the ``RetrievedChunk`` objects produced by the
        vector store (each carries ``chunk_text``/``score``/``chunk_metadata``).
        Implementations score every candidate against ``query``, sort by
        relevance descending, and return at most ``top_n`` of the *same*
        objects (re-scored is fine) so downstream citation rendering is
        unchanged. An empty ``candidates`` list returns ``[]``.
        """
        raise NotImplementedError
