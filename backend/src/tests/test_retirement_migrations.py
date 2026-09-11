"""Fresh and pre-existing schemas in disposable, uniquely named PostgreSQL databases."""
import asyncio
import json
import os
import subprocess
import sys
import uuid

import asyncpg
import pytest
import pytest_asyncio
from sqlalchemy import text

from db.session import create_engine_and_sessionmaker
from services.legacy_cleanup_service import LegacyCleanupService
from stores.vectordb.providers.PgVectorProvider import PgVectorProvider
from tests.conftest import TEST_DATABASE_URL, SRC_DIR, Seeder

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def migration_database():
    # Never drop the configured database: only this generated test database.
    name = "docmind_migration_" + uuid.uuid4().hex
    base = TEST_DATABASE_URL.rsplit("/", 1)[0].replace("postgresql+asyncpg://", "postgresql://", 1)
    maintenance = await asyncpg.connect(base + "/postgres")
    await maintenance.execute(f'CREATE DATABASE "{name}"')
    try:
        yield base + "/" + name
    finally:
        await maintenance.execute(f'DROP DATABASE "{name}" WITH (FORCE)')
        await maintenance.close()


async def migrate(url, target="head", *, success=True):
    result = await asyncio.to_thread(subprocess.run,
        [sys.executable, "-m", "alembic", "upgrade", target], cwd=SRC_DIR,
        env={**os.environ, "DATABASE_URL": url}, capture_output=True, text=True)
    if success:
        assert result.returncode == 0, result.stderr
    else:
        assert result.returncode != 0
    return result


async def test_fresh_database_migrates_without_debug_tables(migration_database):
    await migrate(migration_database)
    provider = PgVectorProvider(migration_database, "cosine")
    await provider.connect()
    try:
        assert await provider.pool.fetchval("SELECT to_regclass('projects')") is None
        assert await provider.pool.fetchval("SELECT to_regclass('idx_embeddings_material')") is not None
        await provider.create_collection("doc_fresh", 3)
        await provider.insert_one("doc_fresh", "New", [1, 0, 0], record_id="new")
    finally:
        await provider.disconnect()


async def test_existing_vectors_survive_adoption_cleanup_and_retirement(migration_database, tmp_path):
    await migrate(migration_database, "0010_active_evaluation_run")
    connection = await asyncpg.connect(migration_database)
    try:
        # Reproduce the previous provider's fixed tables and collection-specific ANN index.
        await connection.execute("""CREATE TABLE vector_collections (
            collection_name VARCHAR PRIMARY KEY, embedding_size INTEGER NOT NULL,
            distance_method VARCHAR NOT NULL DEFAULT 'cosine');
            CREATE TABLE vector_embeddings (id VARCHAR PRIMARY KEY,
            collection_name VARCHAR NOT NULL REFERENCES vector_collections(collection_name) ON DELETE CASCADE,
            text TEXT NOT NULL, metadata JSONB, embedding vector);
            INSERT INTO vector_collections VALUES ('doc_official', 3, 'cosine'), ('collection_old', 3, 'cosine');
            INSERT INTO vector_embeddings VALUES ('official-vector', 'doc_official', 'Keep', '{}', '[1,0,0]'),
                ('legacy-vector', 'collection_old', 'Delete', '{}', '[0,1,0]');
            CREATE INDEX official_ann ON vector_embeddings USING hnsw ((embedding::vector(3)) vector_cosine_ops)
                WHERE collection_name='doc_official'""")
        index_oid = await connection.fetchval("SELECT 'official_ann'::regclass::oid")
    finally:
        await connection.close()
    await migrate(migration_database, "0011_vector_schema")
    root = tmp_path / "uploads"
    legacy_file = root / "old" / "legacy.pdf"
    legacy_file.parent.mkdir(parents=True)
    legacy_file.write_text("legacy", encoding="utf8")
    official_file = root / "official.pdf"
    official_file.write_text("official", encoding="utf8")
    engine, sessions = create_engine_and_sessionmaker(migration_database)
    provider = PgVectorProvider(migration_database, "cosine")
    await provider.connect()
    try:
        async with sessions() as session:
            seed = Seeder(session)
            user = await seed.student()
            await seed.subject(id="official")
            material = await seed.material("official")
            material.storage_path = str(official_file)
            conversation = await seed.doc_conversation(user.id)
            document = await seed.doc_file(conversation.id)
            document.storage_path = str(official_file)
            await session.execute(text("INSERT INTO projects (id,project_id) VALUES (1,'old')"))
            await session.execute(text("""INSERT INTO assets (id,asset_project_id,asset_type,asset_name,asset_config)
                VALUES (1,1,'file','legacy.pdf',CAST(:config AS jsonb))"""),
                {"config": json.dumps({"file_path": str(legacy_file)})})
            await session.execute(text("""INSERT INTO data_chunks (chunk_text,chunk_metadata,chunk_order,chunk_project_id,chunk_asset_id)
                VALUES ('legacy','{}',1,1,1)"""))
            await session.commit()
            failed = await migrate(migration_database, success=False)
            assert "Legacy data remains" in failed.stderr
            assert legacy_file.exists()
            assert await session.scalar(text("SELECT count(*) FROM assets")) == 1
            await LegacyCleanupService(session, provider, root).run(apply=True, manifest=tmp_path / "manifest.json")
        await migrate(migration_database)
        assert not legacy_file.exists() and official_file.exists()
        assert await provider.pool.fetchval("SELECT 'official_ann'::regclass::oid") == index_oid
        assert await provider.pool.fetchval("SELECT count(*) FROM vector_embeddings WHERE id='official-vector'") == 1
        assert await provider.pool.fetchval("SELECT count(*) FROM vector_embeddings WHERE id='legacy-vector'") == 0
        for table in ("users", "materials", "conversations", "document_files"):
            assert await provider.pool.fetchval(f"SELECT count(*) FROM {table}") == 1
        assert await provider.pool.fetchval("SELECT to_regclass('projects')") is None
    finally:
        await provider.disconnect()
        await engine.dispose()
