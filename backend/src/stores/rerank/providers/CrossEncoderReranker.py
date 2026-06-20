"""Local cross-encoder reranker (sentence-transformers).

Scores each ``(query, chunk_text)`` pair with a cross-encoder model that runs
on the backend host (CPU or CUDA). This is the simplest reliable reranker for
the local-Ollama stack: it needs no extra service and runs fully offline.

``sentence-transformers`` (and its ``torch`` dependency) is intentionally kept
out of ``requirements.txt`` to keep the cloud image lean; it is lazily imported
here so the cost is only paid when ``RERANK_BACKEND=LOCAL_CROSS_ENCODER`` is
actually selected (mirroring how an LLM/agent provider is only instantiated
when chosen).
"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

from ..RerankInterface import RerankInterface

logger = logging.getLogger("docmind.rerank.cross_encoder")


class CrossEncoderReranker(RerankInterface):
    def __init__(self, model_id: str, device: Optional[str] = None) -> None:
        if not model_id:
            raise ValueError(
                "RERANK_MODEL_ID is required for the LOCAL_CROSS_ENCODER backend "
                "(e.g. 'BAAI/bge-reranker-base')."
            )
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:  # pragma: no cover - exercised via lazy path
            raise ImportError(
                "The LOCAL_CROSS_ENCODER rerank backend requires the optional "
                "'sentence-transformers' package. Install it with "
                "`pip install sentence-transformers`."
            ) from exc

        self._model_id = model_id
        # device=None lets torch auto-detect (CUDA if present, else CPU).
        self._model = CrossEncoder(model_id, device=device)
        logger.info(
            "CrossEncoderReranker loaded model=%s device=%s",
            model_id,
            device or "auto",
        )

    async def rerank(self, query: str, candidates: List, *, top_n: int) -> List:
        if not candidates:
            return []
        pairs = [(query, getattr(c, "chunk_text", "") or "") for c in candidates]
        # model.predict is sync and CPU/GPU-bound; keep it off the event loop.
        scores = await asyncio.to_thread(self._model.predict, pairs)
        ranked = sorted(
            zip(candidates, scores), key=lambda pair: float(pair[1]), reverse=True
        )
        return [chunk for chunk, _ in ranked[:top_n]]
