import asyncpg
from .BaseDataModel import BaseDataModel
from .db_schemes import Asset


class AssetModel(BaseDataModel):
    def __init__(self, db_pool: asyncpg.Pool):
        super().__init__(db_pool=db_pool)

    @classmethod
    async def create_instance(cls, db_pool: asyncpg.Pool):
        instance = cls(db_pool=db_pool)
        return instance

    def _row_to_asset(self, row) -> Asset:
        return Asset(
            id=row["id"],
            asset_project_id=row["asset_project_id"],
            asset_type=row["asset_type"],
            asset_name=row["asset_name"],
            asset_size=row["asset_size"],
            asset_config=row["asset_config"],
            asset_pushed_at=row["asset_pushed_at"],
        )

    async def create_asset(self, asset: Asset) -> Asset:
        row = await self.db_pool.fetchrow(
            """INSERT INTO assets (asset_project_id, asset_type, asset_name, asset_size, asset_config, asset_pushed_at)
               VALUES ($1, $2, $3, $4, $5, $6)
               RETURNING id, asset_project_id, asset_type, asset_name, asset_size, asset_config, asset_pushed_at""",
            asset.asset_project_id,
            asset.asset_type,
            asset.asset_name,
            asset.asset_size,
            asset.asset_config,
            asset.asset_pushed_at,
        )
        return self._row_to_asset(row)

    async def get_asset_by_id(self, id: int) -> Asset | None:
        row = await self.db_pool.fetchrow(
            "SELECT * FROM assets WHERE id = $1", int(id)
        )
        if row is None:
            return None
        return self._row_to_asset(row)

    async def get_all_project_assets(self, project_id: int, asset_type: str):
        rows = await self.db_pool.fetch(
            "SELECT * FROM assets WHERE asset_project_id = $1 AND asset_type = $2",
            int(project_id),
            asset_type,
        )
        return [self._row_to_asset(row) for row in rows]

    async def get_asset_record(self, asset_name: str, project_id: int) -> Asset | None:
        row = await self.db_pool.fetchrow(
            "SELECT * FROM assets WHERE asset_project_id = $1 AND asset_name = $2",
            int(project_id),
            asset_name,
        )
        if row:
            return self._row_to_asset(row)
        return None
