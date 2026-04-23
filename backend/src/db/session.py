"""Async SQLAlchemy engine and session factory.

The FastAPI app builds a single engine at startup and stores the
``async_sessionmaker`` on ``app.state``. Request-scoped sessions are obtained
via the ``get_session`` dependency (see ``helpers.deps``).
"""
from __future__ import annotations

from typing import AsyncIterator, Tuple

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def _normalize_async_url(url: str) -> str:
    """Ensure the URL targets the async ``asyncpg`` driver."""
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    return url


def create_engine_and_sessionmaker(
    database_url: str,
    echo: bool = False,
) -> Tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Build a new ``AsyncEngine`` + ``async_sessionmaker`` pair."""
    engine = create_async_engine(
        _normalize_async_url(database_url),
        echo=echo,
        pool_pre_ping=True,
    )
    factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
        class_=AsyncSession,
    )
    return engine, factory


async def get_session(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped session. Commits on success, rolls back on error."""
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_session_factory(app) -> async_sessionmaker[AsyncSession]:
    """Return the session factory attached to a FastAPI app at startup."""
    return app.state.session_maker
