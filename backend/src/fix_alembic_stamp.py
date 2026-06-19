"""One-shot script: fix the alembic_version table to point at 0001_initial.

Used when a stale/removed migration left the version tracker pointing at a
revision that no longer exists on disk.

Run: python fix_alembic_stamp.py
"""
import asyncio
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from helpers.config import get_settings


async def main():
    settings = get_settings()
    url = settings.DATABASE_URL
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]

    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE alembic_version SET version_num = '0001_initial'")
        )
    await engine.dispose()
    print("Stamped alembic_version to '0001_initial'")


if __name__ == "__main__":
    asyncio.run(main())
