"""Exercise real adapter persistence, retry and startup failure boundaries."""
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from qdrant_client import models

from services.ingestion_service import IngestedChunk
from services.rag_service import RAGService
from stores.vectordb.errors import VectorStoreError
from stores.vectordb.providers.PgVectorProvider import PgVectorProvider
from stores.vectordb.providers.QdrantDBProvider import QdrantDBProvider
from tests.fakes import FakeLLM
from tests.conftest import TEST_DATABASE_URL


async def test_qdrant_partial_failure_cleans_up_and_retry_does_not_duplicate(tmp_path, monkeypatch):
    provider = QdrantDBProvider(str(tmp_path / "vectors"), "cosine")
    await provider.connect()
    try:
        llm = FakeLLM()
        rag = RAGService(vectordb_client=provider, embedding_client=llm, generation_client=llm, template_parser=None)
        chunks = [IngestedChunk(text=f"Chunk {i}", metadata={}) for i in range(51)]
        await rag.index_chunks("doc_official", [chunks[0]], id_prefix="other-file")
        upsert = provider.client.upsert
        calls = 0
        async def fail_second_batch(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("Provider stopped after persisting the first batch")
            assert kwargs["wait"] is True
            return await upsert(*args, **kwargs)
        monkeypatch.setattr(provider.client, "upsert", fail_second_batch)
        with pytest.raises(VectorStoreError):
            await rag.index_chunks("doc_official", chunks, id_prefix="retry-file")
        assert (await provider.client.count("doc_official")).count == 1
        monkeypatch.setattr(provider.client, "upsert", upsert)
        await rag.index_chunks("doc_official", chunks, id_prefix="retry-file")
        await rag.index_chunks("doc_official", chunks[:2], id_prefix="retry-file")
        assert (await provider.client.count("doc_official")).count == 3
    finally:
        await provider.disconnect()


async def test_qdrant_unconfirmed_write_and_malformed_batch_raise_typed_errors():
    provider = QdrantDBProvider("unused", "cosine")
    provider.client = SimpleNamespace(collection_exists=AsyncMock(return_value=True),
        upsert=AsyncMock(return_value=SimpleNamespace(status=models.UpdateStatus.ACKNOWLEDGED)))
    with pytest.raises(VectorStoreError, match="confirm"):
        await provider.insert_one("collection", "text", [1.0], record_id="id")
    provider.client.upsert.reset_mock()
    with pytest.raises(VectorStoreError):
        await provider.insert_many("collection", ["text"], [], record_ids=["id"])
    provider.client.upsert.assert_not_awaited()


async def test_pgvector_failure_rolls_back_all_batches_and_preserves_other_collections(engine):
    provider = PgVectorProvider(TEST_DATABASE_URL, "cosine")
    await provider.connect()
    try:
        await provider.create_collection("official", 3)
        await provider.create_collection("upload", 3)
        await provider.insert_one("official", "Keep", [1, 0, 0], record_id="shared")
        with pytest.raises(VectorStoreError, match="collide"):
            await provider.insert_many("upload", ["New", "Collision"], [[1, 0, 0], [0, 1, 0]],
                                       record_ids=["new", "shared"], batch_size=1)
        assert (await provider.get_collection_info("upload"))["vectors_count"] == 0
        assert (await provider.get_collection_info("official"))["vectors_count"] == 1
        await provider.insert_many("upload", ["New"], [[1, 0, 0]], record_ids=["new"])
        await provider.insert_many("upload", ["Replaced"], [[1, 0, 0]], record_ids=["new"])
        assert (await provider.get_collection_info("upload"))["vectors_count"] == 1
        assert (await provider.search_by_vector("upload", [1, 0, 0], 1, 0))[0].chunk_text == "Replaced"
    finally:
        await provider.disconnect()


async def test_pgvector_schema_validation_failure_closes_pool_without_ddl(monkeypatch):
    connection = SimpleNamespace(fetch=AsyncMock(side_effect=RuntimeError("missing table")))
    @asynccontextmanager
    async def acquire():
        yield connection
    pool = SimpleNamespace(acquire=acquire, close=AsyncMock())
    monkeypatch.setattr("asyncpg.create_pool", AsyncMock(return_value=pool))
    provider = PgVectorProvider("unused", "cosine")
    with pytest.raises(VectorStoreError, match="migrations"):
        await provider.connect()
    pool.close.assert_awaited_once()
    assert provider.pool is None
    assert connection.fetch.call_args.args[0].startswith("SELECT")


@pytest.mark.parametrize("provider", [PgVectorProvider, QdrantDBProvider])
def test_unsupported_distance_is_a_configuration_error(provider):
    with pytest.raises(ValueError, match="distance"):
        provider("unused", "typo")
