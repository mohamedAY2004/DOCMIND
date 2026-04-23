"""SQLAlchemy 2.0 async ORM layer for DocMind.

Layout:
- ``session`` owns the async engine + session factory.
- ``base`` exposes the declarative ``Base`` used by every model.
- ``models.*`` contains one file per table.

Only ``repositories`` should import from this package. Services talk to
repositories; routes never touch the ORM.
"""
from .base import Base
from .session import (
    create_engine_and_sessionmaker,
    get_session,
    get_session_factory,
)

__all__ = [
    "Base",
    "create_engine_and_sessionmaker",
    "get_session",
    "get_session_factory",
]
