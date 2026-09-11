"""Inventory legacy data; --apply deletes only verified exclusive assets.

Run after upgrading to 0011_vector_schema and before upgrading to head.
The command never starts the API or any generation provider.
"""
import argparse
import asyncio
from pathlib import Path
from db.session import create_engine_and_sessionmaker
from helpers.config import get_settings
from services.legacy_cleanup_service import LegacyCleanupService
from stores.vectordb import VectorDBProviderFactory


async def run(apply, manifest):
    settings = get_settings()
    engine, sessions = create_engine_and_sessionmaker(settings.DATABASE_URL)
    vectors = VectorDBProviderFactory(settings).create(settings.VECTOR_DB_BACKEND)
    try:
        await vectors.connect()
        async with sessions() as session:
            report = await LegacyCleanupService(session, vectors,
                Path(__file__).resolve().parents[1] / "assets" / "files").run(apply=apply, manifest=manifest)
            print(f"Projects: {len(report['projects'])}; blocked: {len(report['blocked'])}; manifest: {manifest}")
            if report["blocked"]:
                raise SystemExit(2)
    finally:
        try:
            await vectors.disconnect()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--manifest", default="legacy-cleanup-manifest.json")
    args = parser.parse_args()
    asyncio.run(run(args.apply, args.manifest))
