"""Startup/shutdown composition with substituted resources, no database required."""
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import FastAPI
import pytest

from tests.fakes import FakeLLM


@pytest.mark.parametrize("failure", [None, "provider", "connect", "shutdown"])
async def test_lifespan_releases_every_created_resource(monkeypatch, failure):
    import main
    config = SimpleNamespace(**main.settings.model_dump())
    config.validate_production = lambda: None
    config.AGENT_ENABLED = config.RERANK_ENABLED = False
    monkeypatch.setattr(main, "settings", config)
    store = SimpleNamespace(close=AsyncMock())
    engine = SimpleNamespace(dispose=AsyncMock())
    @asynccontextmanager
    async def begin():
        yield
    @asynccontextmanager
    async def session():
        yield SimpleNamespace(begin=begin)
    monkeypatch.setattr(main, "create_engine_and_sessionmaker", lambda _: (engine, session))
    monkeypatch.setattr("services.ephemeral_store.build_store", AsyncMock(return_value=store))
    monkeypatch.setattr("repositories.token_blocklist_repository.TokenBlocklistRepository.purge_expired", AsyncMock(return_value=0))
    def llm_factory(_):
        if failure == "provider":
            raise ValueError("Invalid provider")
        return SimpleNamespace(create=lambda _: FakeLLM())
    monkeypatch.setattr(main, "LLMProviderFactory", llm_factory)
    vector = SimpleNamespace(connect=AsyncMock(side_effect=RuntimeError("connect") if failure == "connect" else None),
                             disconnect=AsyncMock(side_effect=RuntimeError("shutdown") if failure == "shutdown" else None))
    monkeypatch.setattr(main, "VectorDBProviderFactory", lambda _: SimpleNamespace(create=lambda **_: vector))
    app = FastAPI()
    if failure:
        with pytest.raises((ValueError, RuntimeError)):
            async with main.lifespan(app):
                pass
    else:
        async with main.lifespan(app):
            assert app.state.session_maker is session
            assert app.state.vectordb_client is vector
            assert not hasattr(app, "db_pool")
    engine.dispose.assert_awaited_once()
    store.close.assert_awaited_once()
    if failure != "provider":
        vector.disconnect.assert_awaited_once()
