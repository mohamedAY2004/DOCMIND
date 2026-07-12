import json
import asyncpg
import numpy as np
from pgvector.asyncpg import register_vector
from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnum
from typing import List, Optional
import logging
from models.db_schemes import RetrievedChunk


class PgVectorProvider(VectorDBInterface):
    DISTANCE_OPERATORS = {
        DistanceMethodEnum.COSINE.value: "<=>",
        DistanceMethodEnum.EUCLID.value: "<->",
        DistanceMethodEnum.DOT.value: "<#>",
        DistanceMethodEnum.MANHATTAN.value: "<+>",
    }

    INDEX_OPS_CLASSES = {
        DistanceMethodEnum.COSINE.value: "vector_cosine_ops",
        DistanceMethodEnum.EUCLID.value: "vector_l2_ops",
        DistanceMethodEnum.DOT.value: "vector_ip_ops",
        DistanceMethodEnum.MANHATTAN.value: "vector_l1_ops",
    }

    def __init__(self, db_url: str, distance_method: str):
        self.db_url = db_url
        self.pool = None
        self.logger = logging.getLogger(__name__)
        self.distance_method = distance_method
        self.distance_operator = self.DISTANCE_OPERATORS.get(distance_method, "<=>")
        self.index_ops_class = self.INDEX_OPS_CLASSES.get(distance_method, "vector_cosine_ops")

    async def connect(self):
        # The extension must exist before the pool's init callback runs register_vector,
        # so install it via a plain connection first.
        bootstrap = await asyncpg.connect(self.db_url)
        try:
            await bootstrap.execute("CREATE EXTENSION IF NOT EXISTS vector")
        finally:
            await bootstrap.close()

        self.pool = await asyncpg.create_pool(self.db_url, init=self._init_connection)
        async with self.pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS vector_collections (
                    collection_name VARCHAR PRIMARY KEY,
                    embedding_size INTEGER NOT NULL,
                    distance_method VARCHAR NOT NULL DEFAULT 'cosine'
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS vector_embeddings (
                    id VARCHAR PRIMARY KEY,
                    collection_name VARCHAR NOT NULL REFERENCES vector_collections(collection_name) ON DELETE CASCADE,
                    text TEXT NOT NULL,
                    metadata JSONB,
                    embedding vector
                )
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_embeddings_collection
                ON vector_embeddings(collection_name)
            """)

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
            if embedding_size <= 2000:
                index_name = f"idx_hnsw_{collection_name.replace('-', '_')}"
                await self.pool.execute(f"""
                    CREATE INDEX IF NOT EXISTS {index_name}
                    ON vector_embeddings
                    USING hnsw ((embedding::vector({embedding_size})) {self.index_ops_class})
                    WHERE collection_name = '{collection_name}'
                """)
            else:
                self.logger.warning(
                    f"Embedding size {embedding_size} exceeds HNSW limit of 2000 dimensions. "
                    f"Skipping index creation for collection '{collection_name}'. "
                    f"Search will use sequential scan."
                )
            return True
        return False

    async def insert_one(self, collection_name: str, text: str, vector: list,
                         metadata: dict = None, record_id: str = None) -> bool:
        if not await self.is_collection_exists(collection_name):
            self.logger.error(f"Collection {collection_name} does not exist to insert record")
            return False
        try:
            embedding = np.array(vector, dtype=np.float32)
            await self.pool.execute(
                """INSERT INTO vector_embeddings (id, collection_name, text, metadata, embedding)
                   VALUES ($1, $2, $3, $4, $5)
                   ON CONFLICT (id) DO UPDATE SET text = $3, metadata = $4, embedding = $5""",
                str(record_id),
                collection_name,
                text,
                metadata,
                embedding,
            )
        except Exception as e:
            self.logger.error(f"Error inserting record into collection {collection_name}: {e}")
            return False
        return True

    async def insert_many(self, collection_name: str, texts: list,
                          vectors: list, metadata: list = None,
                          record_ids: list = None, batch_size: int = 50) -> bool:
        if metadata is None:
            metadata = [None] * len(texts)
        if record_ids is None:
            self.logger.error("Record IDs are required to insert records")
            return False
        if not self.pool:
            self.logger.error("Client is not connected to the database")
            return False
        if not await self.is_collection_exists(collection_name):
            self.logger.error(f"Collection {collection_name} does not exist to insert records")
            return False
        if len(texts) != len(vectors) or len(texts) != len(metadata) or len(texts) != len(record_ids):
            self.logger.error("Length of texts, vectors, metadata, and record_ids must be the same")
            return False

        for i in range(0, len(texts), batch_size):
            batch_end = min(i + batch_size, len(texts))
            batch_data = [
                (
                    str(record_ids[x]),
                    collection_name,
                    texts[x],
                    metadata[x],
                    np.array(vectors[x], dtype=np.float32),
                )
                for x in range(i, batch_end)
            ]
            try:
                await self.pool.executemany(
                    """INSERT INTO vector_embeddings (id, collection_name, text, metadata, embedding)
                       VALUES ($1, $2, $3, $4, $5)
                       ON CONFLICT (id) DO UPDATE SET text = $3, metadata = $4, embedding = $5""",
                    batch_data,
                )
            except Exception as e:
                self.logger.error(f"Error inserting batch of records into collection {collection_name}: {e}")
                return False
        return True

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
                    chunk_metadata=row["metadata"],
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


