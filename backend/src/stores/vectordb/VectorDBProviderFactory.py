from .providers import QdrantDBProvider, PgVectorProvider
from .VectorDBEnums import VectorDBEnums
from helpers.config import Settings


class VectorDBProviderFactory:
    def __init__(self, config: Settings):
        self.config = config

    def create(self, provider: str):
        if provider == VectorDBEnums.QDRANT.value:
            from controllers.BaseController import BaseController
            base_controller = BaseController()
            return QdrantDBProvider(
                db_path=base_controller.get_database_dir(database_name=self.config.VECTOR_DB_PATH),
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
            )
        elif provider == VectorDBEnums.PGVECTOR.value:
            return PgVectorProvider(
                db_url=self.config.DATABASE_URL,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
            )
        return None
