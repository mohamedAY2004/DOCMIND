"""Nightly retention runner; deletion remains opt-in during the report-only week."""
from __future__ import annotations

import asyncio

from helpers.config import get_settings
from scripts.purge_expired_conversations import run


async def main() -> None:
    settings = get_settings()
    while True:
        await run(delete=settings.RETENTION_DELETE_ENABLED)
        await asyncio.sleep(max(60, settings.RETENTION_INTERVAL_SECONDS))


if __name__ == "__main__":
    asyncio.run(main())
