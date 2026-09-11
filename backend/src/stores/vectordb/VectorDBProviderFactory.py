from .providers import QdrantDBProvider, PgVectorProvider
from .VectorDBEnums import VectorDBEnums
from helpers.config import Settings
from pathlib import Path


class VectorDBProviderFactory:
    def __init__(self, config: Settings):
        self.config = config

    def create(self, provider: str):
        if provider == VectorDBEnums.QDRANT.value:
            database_dir = Path(__file__).resolve().parents[2] / "assets" / "database"
            database_path = database_dir / (self.config.VECTOR_DB_PATH or "qdrant")
            database_path.mkdir(parents=True, exist_ok=True)
            return QdrantDBProvider(
                db_path=str(database_path),
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
            )
        elif provider == VectorDBEnums.PGVECTOR.value:
            return PgVectorProvider(
                db_url=self.config.DATABASE_URL,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
            )
        raise ValueError(f"Unsupported vector provider: {provider}")
