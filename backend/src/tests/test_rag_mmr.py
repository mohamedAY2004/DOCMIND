"""Unit tests for MMR diversity selection in ``RAGService.search`` (no DB).

Exercises the Phase-4 over-fetch / MMR-prefilter / soft-degrade behaviour
through the in-memory fakes, plus ``mmr_select`` as a pure function.

Seed geometry (8-dim, query = e0): ``a`` is the most relevant chunk, ``a_dup``
is a near-duplicate of ``a`` (cosine ~0.996) with slightly lower relevance, and
``b`` is diverse (cosine ~0.60 to ``a``) with slightly lower relevance still.
At lambda=0.7 MMR keeps [a, b]; at lambda=1.0 it reduces to vector order
[a, a_dup].
"""
from __future__ import annotations

import pytest

from models.db_schemes import RetrievedChunk
from services.mmr import mmr_select
from services.rag_service import RAGService
from tests.fakes import FakeLLM, FakeReranker, FakeVectorDB

QUERY_VEC = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
VEC_A = [0.8, 0.6, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
VEC_A_DUP = [0.78, 0.62, 0.08, 0.0, 0.0, 0.0, 0.0, 0.0]
VEC_B = [0.75, 0.0, 0.66, 0.0, 0.0, 0.0, 0.0, 0.0]


class _FixedQueryLLM(FakeLLM):
    """FakeLLM whose embeddings are always the fixed query vector, so the
    relevance geometry of hand-seeded chunk vectors is fully controlled."""

    def embed_text(self, text, document_type=None):
        items = [text] if isinstance(text, str) else list(text)
        return [list(QUERY_VEC) for _ in items]


class _SpyVectorDB(FakeVectorDB):
    """FakeVectorDB recording the ``limit``/``with_vectors`` it was called with."""

    def __init__(self) -> None:
        super().__init__()
        self.last_limit: int | None = None
        self.last_with_vectors: bool | None = None

    async def search_by_vector(self, collection_name, vector, limit, threshold,
                               material_ids=None, with_vectors=False):
        self.last_limit = limit
        self.last_with_vectors = with_vectors
        return await super().search_by_vector(
            collection_name, vector, limit, threshold, material_ids=material_ids,
            with_vectors=with_vectors,
        )


class _VectorlessVectorDB(_SpyVectorDB):
    """Simulates a provider that ignores ``with_vectors`` (never returns
    embeddings), to exercise the missing-vector soft-degrade."""

    async def search_by_vector(self, *args, **kwargs):
        results = await super().search_by_vector(*args, **kwargs)
        for chunk in results:
            chunk.embedding = None
        return results


async def _seed_abc(vectordb: FakeVectorDB, collection: str = "c") -> None:
    await vectordb.insert_many(
        collection_name=collection,
        texts=["a", "a_dup", "b"],
        vectors=[VEC_A, VEC_A_DUP, VEC_B],
        metadata=[{}, {}, {}],
        record_ids=["r0", "r1", "r2"],
    )


def _make_rag(vectordb, *, reranker=None, mmr_enabled=True, mmr_lambda=0.7,
              mmr_overfetch=5, overfetch=3, top_n=None) -> RAGService:
    return RAGService(
        vectordb_client=vectordb,
        embedding_client=_FixedQueryLLM(),
        generation_client=FakeLLM(),
        template_parser=None,
        rerank_client=reranker,
        rerank_overfetch=overfetch,
        rerank_top_n=top_n,
        mmr_enabled=mmr_enabled,
        mmr_lambda=mmr_lambda,
        mmr_overfetch=mmr_overfetch,
    )


# --------------------------------------------------------------------------- #
# RAGService.search pipeline behaviour
# --------------------------------------------------------------------------- #

async def test_mmr_drops_near_duplicate() -> None:
    vectordb = _SpyVectorDB()
    await _seed_abc(vectordb)
    rag = _make_rag(vectordb, mmr_lambda=0.7)

    out = await rag.search("c", "q", limit=2, threshold=0.0)

    assert [c.chunk_text for c in out] == ["a", "b"]
    assert vectordb.last_with_vectors is True


async def test_lambda_one_is_pure_relevance() -> None:
    vectordb = _SpyVectorDB()
    await _seed_abc(vectordb)
    rag = _make_rag(vectordb, mmr_lambda=1.0)

    out = await rag.search("c", "q", limit=2, threshold=0.0)

    assert [c.chunk_text for c in out] == ["a", "a_dup"]


async def test_fetch_and_pool_sizes() -> None:
    texts = [f"doc {i}" for i in range(30)]
    vectors = [list(QUERY_VEC) for _ in texts]
    vectordb = _SpyVectorDB()
    await vectordb.insert_many(
        collection_name="c", texts=texts, vectors=vectors,
        metadata=[{} for _ in texts], record_ids=[f"r{i}" for i in range(len(texts))],
    )
    reranker = FakeReranker()

    # keep = limit = 3 -> raw fetch = 3 * mmr_overfetch = 15, rerank keeps 3.
    rag = _make_rag(vectordb, reranker=reranker, mmr_overfetch=5, overfetch=3)
    out = await rag.search("c", "q", limit=3, threshold=0.0)
    assert vectordb.last_limit == 15
    assert reranker.last_top_n == 3
    assert len(out) == 3

    # rerank_top_n overrides limit as ``keep``: fetch = 4 * 5 = 20.
    rag = _make_rag(vectordb, reranker=reranker, mmr_overfetch=5, overfetch=3,
                    top_n=4)
    out = await rag.search("c", "q", limit=3, threshold=0.0)
    assert vectordb.last_limit == 20
    assert reranker.last_top_n == 4
    assert len(out) == 4


async def test_mmr_plus_rerank_order_follows_reranker() -> None:
    vectordb = _SpyVectorDB()
    await _seed_abc(vectordb)
    # With overfetch=1 the MMR pool == keep (2), so MMR really prunes: it hands
    # [a, b] (duplicate dropped) to the reranker, which then promotes "b".
    reranker = FakeReranker(score_map={"b": 10, "a": 5})
    rag = _make_rag(vectordb, reranker=reranker, mmr_lambda=0.7, top_n=2,
                    overfetch=1)

    out = await rag.search("c", "q", limit=2, threshold=0.0)

    assert [c.chunk_text for c in out] == ["b", "a"]
    assert len(out) == 2


async def test_missing_vectors_soft_degrades() -> None:
    vectordb = _VectorlessVectorDB()
    await _seed_abc(vectordb)
    rag = _make_rag(vectordb, mmr_lambda=0.7)

    out = await rag.search("c", "q", limit=2, threshold=0.0)

    # Without embeddings MMR falls back to plain vector order, never raises.
    assert [c.chunk_text for c in out] == ["a", "a_dup"]


async def test_mmr_exception_soft_degrades(monkeypatch: pytest.MonkeyPatch) -> None:
    vectordb = _SpyVectorDB()
    await _seed_abc(vectordb)
    rag = _make_rag(vectordb, mmr_lambda=0.7)

    def _boom(*args, **kwargs):
        raise RuntimeError("mmr exploded")

    monkeypatch.setattr("services.rag_service.mmr_select", _boom)
    out = await rag.search("c", "q", limit=2, threshold=0.0)

    assert [c.chunk_text for c in out] == ["a", "a_dup"]


async def test_mmr_off_path_unchanged() -> None:
    vectordb = _SpyVectorDB()
    await _seed_abc(vectordb)
    rag = _make_rag(vectordb, mmr_enabled=False)

    out = await rag.search("c", "q", limit=2, threshold=0.0)

    # No over-fetch, no vector fetch, plain vector order.
    assert vectordb.last_limit == 2
    assert vectordb.last_with_vectors is False
    assert [c.chunk_text for c in out] == ["a", "a_dup"]


# --------------------------------------------------------------------------- #
# mmr_select as a pure function
# --------------------------------------------------------------------------- #

def _chunk(text: str, embedding=None) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_text=text, score=1.0, chunk_metadata={}, embedding=embedding
    )


def test_mmr_select_empty_and_zero_k() -> None:
    assert mmr_select(QUERY_VEC, [], k=3) == []
    assert mmr_select(QUERY_VEC, [_chunk("a", VEC_A)], k=0) == []


def test_mmr_select_k_at_least_n_is_identity() -> None:
    candidates = [_chunk("a", VEC_A), _chunk("b", VEC_B)]
    assert mmr_select(QUERY_VEC, candidates, k=2) == candidates
    assert mmr_select(QUERY_VEC, candidates, k=5) == candidates


def test_mmr_select_missing_embedding_falls_back_to_truncation() -> None:
    candidates = [_chunk("a", VEC_A), _chunk("no_vec", None), _chunk("b", VEC_B)]
    out = mmr_select(QUERY_VEC, candidates, k=2)
    assert out == candidates[:2]  # original order, no reordering attempted


def test_mmr_select_zero_norm_vector_does_not_crash() -> None:
    zero = [0.0] * 8
    candidates = [_chunk("a", VEC_A), _chunk("zero", zero), _chunk("b", VEC_B)]
    out = mmr_select(QUERY_VEC, candidates, k=2, lambda_mult=0.7)
    assert len(out) == 2
    assert out[0].chunk_text == "a"  # highest relevance still selected first
