import asyncpg
from .BaseDataModel import BaseDataModel
from .db_schemes import DataChunk


class ChunkModel(BaseDataModel):
    def __init__(self, db_pool: asyncpg.Pool):
        super().__init__(db_pool=db_pool)

    @classmethod
    async def create_instance(cls, db_pool: asyncpg.Pool):
        instance = cls(db_pool=db_pool)
        return instance

    def _row_to_chunk(self, row) -> DataChunk:
        return DataChunk(
            id=row["id"],
            chunk_text=row["chunk_text"],
            chunk_metadata=row["chunk_metadata"],
            chunk_order=row["chunk_order"],
            chunk_project_id=row["chunk_project_id"],
            chunk_asset_id=row["chunk_asset_id"],
        )

    async def create_chunk(self, chunk: DataChunk) -> DataChunk:
        row = await self.db_pool.fetchrow(
            """INSERT INTO data_chunks (chunk_text, chunk_metadata, chunk_order, chunk_project_id, chunk_asset_id)
               VALUES ($1, $2, $3, $4, $5)
               RETURNING *""",
            chunk.chunk_text,
            chunk.chunk_metadata,
            chunk.chunk_order,
            chunk.chunk_project_id,
            chunk.chunk_asset_id,
        )
        return self._row_to_chunk(row)

    async def get_chunk_by_id(self, id: int) -> DataChunk | None:
        row = await self.db_pool.fetchrow(
            "SELECT * FROM data_chunks WHERE id = $1", int(id)
        )
        if row is None:
            return None
        return self._row_to_chunk(row)

    async def insert_many_chunks(self, chunks: list[DataChunk], batch_size: int = 100) -> int:
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            await self.db_pool.executemany(
                """INSERT INTO data_chunks (chunk_text, chunk_metadata, chunk_order, chunk_project_id, chunk_asset_id)
                   VALUES ($1, $2, $3, $4, $5)""",
                [
                    (
                        chunk.chunk_text,
                        chunk.chunk_metadata,
                        chunk.chunk_order,
                        chunk.chunk_project_id,
                        chunk.chunk_asset_id,
                    )
                    for chunk in batch
                ],
            )
        return len(chunks)

    async def delete_chunks_by_project_id(self, project_id: int) -> int:
        result = await self.db_pool.execute(
            "DELETE FROM data_chunks WHERE chunk_project_id = $1", int(project_id)
        )
        count_str = result.split(" ")[-1]
        return int(count_str)

    async def get_chunks_by_project_id(self, project_id: int, page: int = 1, page_size: int = 100):
        offset = (page - 1) * page_size
        rows = await self.db_pool.fetch(
            """SELECT * FROM data_chunks
               WHERE chunk_project_id = $1
               ORDER BY id
               LIMIT $2 OFFSET $3""",
            int(project_id),
            page_size,
            offset,
        )
        return [self._row_to_chunk(row) for row in rows]
