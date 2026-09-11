"""Behavioral regressions for provider contracts and retired/debug access."""
from types import SimpleNamespace

import pytest

from services.ingestion_service import IngestedChunk
from services.rag_service import RAGService
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.providers.QdrantDBProvider import QdrantDBProvider
from tests.conftest import auth_header
from tests.fakes import FakeLLM, FakeVectorDB


def test_cohere_factory_constructs_advertised_provider():
    settings = SimpleNamespace(COHERE_API_KEY="test", DEFAULT_INPUT_MAX_CHARACTERS=1000,
                               DEFAULT_GENERATION_MAX_TOKENS=100, DEFAULT_GENERATION_TEMPERATURE=0.1)
    assert LLMProviderFactory(settings).create("COHERE").generation_model_id is None


def test_unknown_provider_fails_clearly():
    with pytest.raises(ValueError, match="provider"):
        LLMProviderFactory(SimpleNamespace()).create("TYPO")


def test_qdrant_accepts_official_ids_and_preserves_uuids():
    provider = QdrantDBProvider("unused", "cosine")
    value = "tutor_example_0123456789abcdef_0"
    assert provider._to_qdrant_id(value) == provider._to_qdrant_id(value)
    assert provider._to_qdrant_id(value) != provider._to_qdrant_id(value + "1")
    uuid = "550e8400-e29b-41d4-a716-446655440000"
    assert provider._to_qdrant_id(uuid) == uuid


async def test_failed_vector_write_cannot_report_indexed():
    class FailedStore(FakeVectorDB):
        async def insert_many(self, **kwargs):
            return False

    rag = RAGService(vectordb_client=FailedStore(), embedding_client=FakeLLM(),
                     generation_client=FakeLLM(), template_parser=None)
    with pytest.raises(Exception, match="write|persist"):
        await rag.index_chunks("doc_test", [IngestedChunk(text="hello", metadata={})])


@pytest.mark.parametrize("suffix", ["", "/stream"])
async def test_preview_rejects_unrelated_instructor(client, seed, suffix):
    owner = await seed.instructor()
    outsider = await seed.instructor()
    await seed.subject(id="preview-scope", instructors=[owner])
    await seed.material("preview-scope", name="Private material")
    response = await client.post(f"/api/subjects/preview-scope/test-bot{suffix}",
                                json={"message": "Explain this"}, headers=auth_header(outsider))
    assert response.status_code == 403


async def test_debug_endpoints_are_removed(client):
    for path in ["/api/v1/data/process/example", "/api/v1/nlp/index/search/example"]:
        response = await client.post(path, json={})
        assert response.status_code == 404
