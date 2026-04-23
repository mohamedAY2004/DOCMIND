import asyncpg
from .BaseDataModel import BaseDataModel
from .db_schemes import Project


class ProjectModel(BaseDataModel):
    def __init__(self, db_pool: asyncpg.Pool):
        super().__init__(db_pool=db_pool)

    @classmethod
    async def create_instance(cls, db_pool: asyncpg.Pool):
        instance = cls(db_pool=db_pool)
        return instance

    async def create_project(self, project: Project) -> Project:
        row = await self.db_pool.fetchrow(
            "INSERT INTO projects (project_id) VALUES ($1) RETURNING id, project_id",
            project.project_id,
        )
        return Project(id=row["id"], project_id=row["project_id"])

    async def get_project_or_create_one(self, project_id: str) -> Project:
        row = await self.db_pool.fetchrow(
            "SELECT id, project_id FROM projects WHERE project_id = $1", project_id
        )
        if row is None:
            project = Project(project_id=project_id)
            return await self.create_project(project=project)
        return Project(id=row["id"], project_id=row["project_id"])

    async def get_all_projects(self, page: int = 1, page_size: int = 10):
        total_records = await self.db_pool.fetchval("SELECT COUNT(*) FROM projects")
        total_pages = (total_records + page_size - 1) // page_size

        offset = (page - 1) * page_size
        rows = await self.db_pool.fetch(
            "SELECT id, project_id FROM projects ORDER BY id LIMIT $1 OFFSET $2",
            page_size,
            offset,
        )
        projects = [Project(id=row["id"], project_id=row["project_id"]) for row in rows]
        return projects, total_pages
