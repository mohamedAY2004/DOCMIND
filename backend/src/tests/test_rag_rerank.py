"""Unit tests for cross-encoder reranking in ``RAGService.search`` (no DB).

Exercises the Phase-3 over-fetch / truncate / soft-degrade behaviour through
the in-memory fakes, plus the rerank provider factory.
"""
from __future__ import annotations

import pytest

from services.rag_service import RAGService
from stores.rerank.RerankProviderFactory import RerankProviderFactory
from tests.fakes import FakeLLM, FakeReranker, FakeVectorDB


class _SpyVectorDB(FakeVectorDB):
    """FakeVectorDB that records the ``limit`` passed to ``search_by_vector``."""

    def __init__(self) -> None:
        super().__init__()
        self.last_limit: int | None = None
        self.last_material_ids = None

    async def search_by_vector(self, collection_name, vector, limit, threshold,
                               material_ids=None, with_vectors=False):
        self.last_limit = limit
        self.last_material_ids = material_ids
        return await super().search_by_vector(
            collection_name, vector, limit, threshold, material_ids=material_ids,
            with_vectors=with_vectors,
        )


async def _seed(vectordb: FakeVectorDB, collection: str, texts, material_ids=None):
    embed = FakeLLM()
    vectors = embed.embed_text(texts)
    metas = [
        {"material_id": material_ids[i]} if material_ids else {}
        for i in range(len(texts))
    ]
    await vectordb.insert_many(
        collection_name=collection,
        texts=texts,
        vectors=vectors,
        metadata=metas,
        record_ids=[f"r{i}" for i in range(len(texts))],
    )


def _make_rag(vectordb, reranker, *, overfetch=3, top_n=None) -> RAGService:
    return RAGService(
        vectordb_client=vectordb,
        embedding_client=FakeLLM(),
        generation_client=FakeLLM(),
        template_parser=None,
        rerank_client=reranker,
        rerank_overfetch=overfetch,
        rerank_top_n=top_n,
    )


async def test_overfetch_and_truncation_follows_rerank_order() -> None:
    texts = [f"doc {i}" for i in range(9)]
    vectordb = _SpyVectorDB()
    await _seed(vectordb, "c", texts)

    # Make "doc 7" then "doc 3" the most relevant regardless of vector order.
    reranker = FakeReranker(score_map={"doc 7": 10, "doc 3": 5})
    rag = _make_rag(vectordb, reranker, overfetch=3)

    out = await rag.search("c", "q", limit=3, threshold=0.0)

    # (a) over-fetch = limit * overfetch ; (b) truncated to limit
    assert vectordb.last_limit == 9
    assert len(out) == 3
    # (c) order follows reranker score
    assert out[0].chunk_text == "doc 7"
    assert out[1].chunk_text == "doc 3"
    assert reranker.last_top_n == 3


async def test_top_n_overrides_limit() -> None:
    texts = [f"doc {i}" for i in range(12)]
    vectordb = _SpyVectorDB()
    await _seed(vectordb, "c", texts)
    rag = _make_rag(vectordb, FakeReranker(), overfetch=2, top_n=4)

    out = await rag.search("c", "q", limit=3, threshold=0.0)

    assert vectordb.last_limit == 8  # keep(=top_n 4) * overfetch 2
    assert len(out) == 4


async def test_material_ids_forwarded_through_rerank_path() -> None:
    texts = ["alpha", "beta", "gamma"]
    vectordb = _SpyVectorDB()
    await _seed(vectordb, "c", texts, material_ids=["m1", "m2", "m3"])
    rag = _make_rag(vectordb, FakeReranker())

    out = await rag.search("c", "q", limit=2, threshold=0.0, material_ids=["m2"])

    assert vectordb.last_material_ids == ["m2"]
    assert {c.chunk_text for c in out} == {"beta"}


async def test_reranker_failure_degrades_to_vector_order() -> None:
    texts = [f"doc {i}" for i in range(6)]
    vectordb = _SpyVectorDB()
    await _seed(vectordb, "c", texts)
    rag = _make_rag(vectordb, FakeReranker(raises=True), overfetch=2)

    out = await rag.search("c", "q", limit=3, threshold=0.0)

    # Soft-degrade: never raises, returns top `limit` in vector order.
    assert len(out) == 3


async def test_no_rerank_client_uses_limit_directly() -> None:
    texts = [f"doc {i}" for i in range(6)]
    vectordb = _SpyVectorDB()
    await _seed(vectordb, "c", texts)
    rag = RAGService(
        vectordb_client=vectordb,
        embedding_client=FakeLLM(),
        generation_client=FakeLLM(),
        template_parser=None,
    )

    out = await rag.search("c", "q", limit=3, threshold=0.0)

    assert vectordb.last_limit == 3  # no over-fetch
    assert len(out) == 3


# ----------------------------- factory -----------------------------


def test_factory_unknown_backend_raises() -> None:
    from helpers.config import get_settings

    factory = RerankProviderFactory(get_settings())
    with pytest.raises(ValueError):
        factory.create("NOPE")


def test_factory_builds_local_cross_encoder(monkeypatch) -> None:
    """LOCAL_CROSS_ENCODER constructs without the heavy dep installed.

    We stub the provider's lazy ``CrossEncoder`` import so the factory wiring is
    tested even on machines without sentence-transformers.
    """
    import sys
    import types

    fake_mod = types.ModuleType("sentence_transformers")

    class _StubCE:
        def __init__(self, model_id, device=None):
            self.model_id = model_id

        def predict(self, pairs):
            return [0.0 for _ in pairs]

    fake_mod.CrossEncoder = _StubCE
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_mod)

    from helpers.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "RERANK_MODEL_ID", "stub-model", raising=False)
    factory = RerankProviderFactory(settings)
    provider = factory.create("LOCAL_CROSS_ENCODER")
    assert provider is not None
