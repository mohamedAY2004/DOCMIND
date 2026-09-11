"""Inventory queries used exclusively by the one-time legacy retirement command."""
from sqlalchemy import text


class LegacyCleanupRepository:
    def __init__(self, session):
        self.session = session

    async def _exists(self, table):
        return (await self.session.execute(text("SELECT to_regclass(:table)"), {"table": "public." + table})).scalar() is not None

    async def inventory(self):
        if not await self._exists("projects"):
            return []
        projects = (await self.session.execute(text("SELECT id, project_id FROM projects ORDER BY id"))).mappings().all()
        assets = ((await self.session.execute(text("SELECT id, asset_project_id, asset_type, asset_name, asset_config FROM assets ORDER BY id"))).mappings().all()
                  if await self._exists("assets") else [])
        chunks = dict((await self.session.execute(text("SELECT chunk_project_id, count(*) FROM data_chunks GROUP BY chunk_project_id"))).all()) if await self._exists("data_chunks") else {}
        return [dict(p, assets=[dict(a) for a in assets if a["asset_project_id"] == p["id"]],
                     chunk_count=chunks.get(p["id"], 0)) for p in projects]

    async def protected_paths(self):
        # Missing official tables is an error, never permission to skip protection.
        rows = await self.session.execute(text("SELECT storage_path FROM materials UNION SELECT storage_path FROM document_files"))
        return list(rows.scalars())

    async def remove_project(self, project_id):
        for table, column in (("data_chunks", "chunk_project_id"), ("assets", "asset_project_id"), ("projects", "id")):
            if await self._exists(table):
                await self.session.execute(text(f"DELETE FROM {table} WHERE {column}=:id"), {"id": project_id})
