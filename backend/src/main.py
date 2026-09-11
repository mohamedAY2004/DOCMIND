"""DocMind official API. Schema changes are owned by Alembic."""
from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.session import create_engine_and_sessionmaker
from helpers.config import get_settings
from helpers.errors import install_exception_handlers
from helpers.middleware import CSRFMiddleware, RateLimitMiddleware, RequestIDMiddleware
from routes.admin_router import (
    activity_router,
    analytics_router,
    feedback_router,
    subjects_stats_router,
    users_router,
)
from routes.auth_router import router as auth_router
from routes.chat_doc_router import legacy_router as chat_doc_compat_router
from routes.chat_doc_router import router as chat_doc_router
from routes.chat_feedback_router import router as chat_feedback_router
from routes.chat_feedback_router import content_router as citation_content_router
from routes.chat_tutor_router import legacy_router as chat_tutor_compat_router
from routes.chat_tutor_router import router as chat_tutor_router
from routes.health import router as health_router
from routes.evaluation_router import admin_router as admin_evaluation_router
from routes.evaluation_router import router as evaluation_router
from routes.materials_router import router as materials_router
from routes.subjects_router import (
    admin_semesters_router,
    admin_subjects_router,
    semesters_router,
    subjects_router,
)
from routes.system_access_router import admin_router as admin_system_router
from routes.system_access_router import public_router as public_system_router
from stores.agent import AgentProviderFactory
from stores.llm import LLMProviderFactory
from stores.llm.templates.TemplateParser import TemplateParser
from stores.rerank import RerankProviderFactory
from stores.vectordb import VectorDBProviderFactory

logger = logging.getLogger("docmind")

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as resources:
        settings.validate_production()
        from services.ephemeral_store import build_store
        app.state.ephemeral_store = await build_store(settings.REDIS_URL)
        resources.push_async_callback(app.state.ephemeral_store.close)
        # ----- SQLAlchemy async engine + sessionmaker (DocMind API) -----
        engine, session_maker = create_engine_and_sessionmaker(settings.DATABASE_URL)
        resources.push_async_callback(engine.dispose)
        app.state.engine = engine
        app.state.session_maker = session_maker

        # Drop already-expired token-blocklist rows on boot so the table doesn't grow
        # unbounded. A scheduled job is the longer-term home for this sweep.
        try:
            from datetime import datetime, timezone

            from repositories.token_blocklist_repository import TokenBlocklistRepository

            async with session_maker() as session:
                async with session.begin():
                    removed = await TokenBlocklistRepository(session).purge_expired(
                        datetime.now(timezone.utc)
                    )
            logger.info("Purged %d expired token-blocklist rows on startup", removed)
        except Exception:  # noqa: BLE001
            logger.exception("Token-blocklist purge on startup failed")

        # ----- LLM + VectorDB + Templates -----
        llm_factory = LLMProviderFactory(settings)
        app.state.generation_client = llm_factory.create(settings.GENERATION_BACKEND)
        app.state.generation_client.set_generation_model(settings.GENERATION_MODEL_ID)

        app.state.embedding_client = llm_factory.create(settings.EMBEDDING_BACKEND)
        app.state.embedding_client.set_embedding_model(
            settings.EMBEDDING_MODEL_ID, settings.EMBEDDING_SIZE
        )

        vector_factory = VectorDBProviderFactory(settings)
        app.state.vectordb_client = vector_factory.create(provider=settings.VECTOR_DB_BACKEND)
        resources.push_async_callback(app.state.vectordb_client.disconnect)
        await app.state.vectordb_client.connect()

        app.state.template_parser = TemplateParser(language=settings.DEFAULT_LANGUAGE)

        # ----- Agentic RAG layer (optional; ``AGENT_ENABLED`` in .env) -----
        if settings.AGENT_ENABLED and settings.AGENT_STRATEGY:
            agent_factory = AgentProviderFactory(settings)
            app.state.agent_client = agent_factory.create(
                settings.AGENT_STRATEGY,
                generation_client=app.state.generation_client,
                template_parser=app.state.template_parser,
            )
            logger.info(
                "Agentic RAG enabled with strategy=%s", settings.AGENT_STRATEGY
            )
        else:
            app.state.agent_client = None

        # ----- Reranking layer (optional; ``RERANK_ENABLED`` in .env) -----
        if settings.RERANK_ENABLED and settings.RERANK_BACKEND:
            rerank_factory = RerankProviderFactory(settings)
            app.state.rerank_client = rerank_factory.create(settings.RERANK_BACKEND)
            logger.info(
                "Reranking enabled with backend=%s model=%s",
                settings.RERANK_BACKEND,
                settings.RERANK_MODEL_ID,
            )
        else:
            app.state.rerank_client = None

        # ----- MMR diversity prefilter (optional; ``MMR_ENABLED`` in .env) -----
        # Pure function, no client object — logged here for startup visibility.
        if settings.MMR_ENABLED:
            logger.info(
                "MMR diversity enabled lambda=%s overfetch=%s",
                settings.MMR_LAMBDA,
                settings.MMR_OVERFETCH,
            )

        yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(CSRFMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "X-Request-Id", "X-CSRF-Token"],
    expose_headers=["X-Request-Id"],
)

install_exception_handlers(app)


# -------------------- routers --------------------

# Public (no /api prefix) — /health is documented as top-level per spec §3.5.
app.include_router(health_router)

# DocMind public API (spec §4–§10).
app.include_router(auth_router, prefix="/api")
app.include_router(public_system_router, prefix="/api")
app.include_router(admin_system_router, prefix="/api")
app.include_router(subjects_router, prefix="/api")
app.include_router(admin_subjects_router, prefix="/api")
app.include_router(semesters_router, prefix="/api")
app.include_router(admin_semesters_router, prefix="/api")
app.include_router(materials_router, prefix="/api")
app.include_router(evaluation_router, prefix="/api")
app.include_router(admin_evaluation_router, prefix="/api")
app.include_router(chat_doc_router, prefix="/api")
app.include_router(chat_doc_compat_router, prefix="/api")
app.include_router(chat_tutor_router, prefix="/api")
app.include_router(chat_tutor_compat_router, prefix="/api")
app.include_router(chat_feedback_router, prefix="/api")
app.include_router(citation_content_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(subjects_stats_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")
app.include_router(activity_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
