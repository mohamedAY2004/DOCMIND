import json
import asyncpg
import numpy as np
from pgvector.asyncpg import register_vector
from ..VectorDBInterface import VectorDBInterface
from ..errors import VectorStoreError, vector_write, validate_batch
from ..VectorDBEnums import DistanceMethodEnum
from typing import List, Optional
import logging
from stores.vectordb.types import RetrievedChunk


class PgVectorProvider(VectorDBInterface):
    DISTANCE_OPERATORS = {
        DistanceMethodEnum.COSINE.value: "<=>",
        DistanceMethodEnum.EUCLID.value: "<->",
        DistanceMethodEnum.DOT.value: "<#>",
        DistanceMethodEnum.MANHATTAN.value: "<+>",
    }

    def __init__(self, db_url: str, distance_method: str):
        self.db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        self.pool = None
        self.logger = logging.getLogger(__name__)
        self.distance_method = distance_method
        if distance_method not in self.DISTANCE_OPERATORS:
            raise ValueError(f"Unsupported vector distance method: {distance_method}")
        self.distance_operator = self.DISTANCE_OPERATORS[distance_method]

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(self.db_url, init=self._init_connection)
            async with self.pool.acquire() as conn:
                # SELECT validates required columns without mutating any schema or rows.
                await conn.fetch("SELECT collection_name, embedding_size, distance_method FROM vector_collections LIMIT 0")
                await conn.fetch("SELECT id, collection_name, text, metadata, embedding FROM vector_embeddings LIMIT 0")
                valid = await conn.fetchval("""SELECT count(*)=1 FROM pg_attribute
                    WHERE attrelid='vector_embeddings'::regclass AND attname='embedding'
                      AND atttypid='vector'::regtype AND atttypmod=-1""")
                if not valid:
                    raise VectorStoreError("Vector schema is incompatible; run Alembic migrations")
        except Exception as exc:
            await self.disconnect()
            raise VectorStoreError("Vector schema unavailable; run Alembic migrations before startup") from exc

    @staticmethod
    async def _init_connection(conn):
        await register_vector(conn)
        await conn.set_type_codec(
            "jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
        )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def is_collection_exists(self, collection_name: str) -> bool:
        row = await self.pool.fetchrow(
            "SELECT 1 FROM vector_collections WHERE collection_name = $1",
            collection_name,
        )
        return row is not None

    async def list_all_collections(self) -> List:
        rows = await self.pool.fetch("SELECT collection_name FROM vector_collections")
        return [row["collection_name"] for row in rows]

    async def get_collection_info(self, collection_name: str) -> dict:
        coll_row = await self.pool.fetchrow(
            "SELECT * FROM vector_collections WHERE collection_name = $1",
            collection_name,
        )
        if not coll_row:
            return {}
        count = await self.pool.fetchval(
            "SELECT COUNT(*) FROM vector_embeddings WHERE collection_name = $1",
            collection_name,
        )
        return {
            "collection_name": coll_row["collection_name"],
            "embedding_size": coll_row["embedding_size"],
            "distance_method": coll_row["distance_method"],
            "vectors_count": count,
        }

    async def delete_collection(self, collection_name: str):
        if await self.is_collection_exists(collection_name):
            await self.pool.execute(
                "DELETE FROM vector_collections WHERE collection_name = $1",
                collection_name,
            )
            return True
        return False

    async def create_collection(self, collection_name: str, embedding_size: int, do_reset: bool = False) -> bool:
        if do_reset:
            await self.delete_collection(collection_name)
        if not await self.is_collection_exists(collection_name):
            await self.pool.execute(
                """INSERT INTO vector_collections (collection_name, embedding_size, distance_method)
                   VALUES ($1, $2, $3)""",
                collection_name,
                embedding_size,
                self.distance_method,
            )
            return True
        return False

    async def insert_one(self, collection_name: str, text: str, vector: list,
                         metadata: dict = None, record_id: str = None) -> None:
        await self.insert_many(collection_name, [text], [vector], [metadata], [record_id])

    async def insert_many(self, collection_name: str, texts: list, vectors: list,
                          metadata: list = None, record_ids: list = None,
                          batch_size: int = 50) -> None:
        with vector_write():
            metadata = metadata if metadata is not None else [None] * len(texts)
            validate_batch(texts, vectors, metadata, record_ids, batch_size)
            if not await self.is_collection_exists(collection_name):
                raise VectorStoreError(f"Collection {collection_name} does not exist")
            # Convert the full input before any writes, then commit every batch together.
            rows = [(record_ids[i], collection_name, text, metadata[i],
                     np.asarray(vectors[i], dtype=np.float32)) for i, text in enumerate(texts)]
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    for start in range(0, len(rows), batch_size):
                        await conn.executemany(
                            """INSERT INTO vector_embeddings (id, collection_name, text, metadata, embedding)
                               VALUES ($1, $2, $3, $4, $5)
                               ON CONFLICT (id) DO UPDATE SET text = $3, metadata = $4, embedding = $5
                               WHERE vector_embeddings.collection_name = EXCLUDED.collection_name""",
                            rows[start:start + batch_size],
                        )
                        # Global IDs must never silently collide with another collection.
                        persisted = await conn.fetchval(
                            "SELECT count(*) FROM vector_embeddings WHERE collection_name=$1 AND id=ANY($2::varchar[])",
                            collection_name, record_ids[start:start + batch_size],
                        )
                        if persisted != len(rows[start:start + batch_size]):
                            raise VectorStoreError("Vector IDs collide with another collection")

    async def delete_by_material_id(self, collection_name: str, material_id: str) -> bool:
        if not await self.is_collection_exists(collection_name):
            return False
        # Chunks are stamped with metadata.material_id at index time; the id
        # LIKE clause additionally catches chunks indexed before stamping
        # existed (record ids embed the material id as a prefix).
        legacy_id_pattern = f"{collection_name}_{material_id.replace('-', '')}_%"
        result = await self.pool.execute(
            """DELETE FROM vector_embeddings
               WHERE collection_name = $1
                 AND (metadata->>'material_id' = $2 OR id LIKE $3)""",
            collection_name,
            material_id,
            legacy_id_pattern,
        )
        self.logger.info(
            "Deleted chunks for material %s in collection %s: %s",
            material_id, collection_name, result,
        )
        return True

    async def search_by_vector(self, collection_name: str, vector: list,
                               limit: int, threshold: float = 0.5,
                               material_ids: Optional[List[str]] = None,
                               with_vectors: bool = False) -> List[RetrievedChunk]:
        if not await self.is_collection_exists(collection_name):
            self.logger.error(f"Collection {collection_name} does not exist to search records")
            return None

        embedding = np.array(vector, dtype=np.float32)
        op = self.distance_operator

        # Optional scope to specific owning materials. Kept as a separate
        # parameterised clause so the unscoped query path is byte-identical to
        # before; the JSONB key is stamped at index time by RAGService.
        params = [embedding, collection_name, threshold, limit]
        source_clause = ""
        if material_ids:
            params.append(list(material_ids))
            source_clause = f"AND metadata->>'material_id' = ANY(${len(params)})"

        # Only select the stored vectors when the caller (MMR) needs them, so
        # the default query stays byte-identical to before.
        embed_col = ", embedding" if with_vectors else ""
        query = f"""
            SELECT text, metadata,
                   1 - (embedding {op} $1::vector) AS score{embed_col}
            FROM vector_embeddings
            WHERE collection_name = $2
              AND 1 - (embedding {op} $1::vector) >= $3
              {source_clause}
            ORDER BY embedding {op} $1::vector
            LIMIT $4
        """
        rows = await self.pool.fetch(query, *params)

        if rows:
            return [
                RetrievedChunk(
                    chunk_text=row["text"],
                    score=float(row["score"]),
                    chunk_metadata=row["metadata"] or {},
                    embedding=_coerce_embedding(row["embedding"]) if with_vectors else None,
                )
                for row in rows
            ]
        return None


def _coerce_embedding(value) -> Optional[list]:
    """Normalise a pgvector column value to ``list[float]``.

    The pool registers the pgvector codec (``register_vector`` in
    ``_init_connection``) so ``value`` is normally an ``np.ndarray``; the other
    forms are accepted defensively in case the codec is ever not registered.
    """
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (list, tuple)):
        return [float(v) for v in value]
    if isinstance(value, str):  # "[0.1,0.2,...]"
        try:
            return [float(v) for v in value.strip("[]").split(",") if v.strip()]
        except ValueError:
            return None
    return None


