from abc import ABC, abstractmethod
from typing import List, Optional
from models.db_schemes import RetrievedChunk
class VectorDBInterface(ABC):

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def is_collection_exists(self, collection_name: str) -> bool:
        pass

    @abstractmethod
    async def list_all_collections(self) -> List:
        pass

    @abstractmethod
    async def get_collection_info(self, collection_name: str) -> dict:
        pass

    @abstractmethod
    async def delete_collection(self, collection_name: str):
        pass

    @abstractmethod
    async def create_collection(self, collection_name: str, 
                                embedding_size: int,
                                do_reset: bool = False):
        pass

    @abstractmethod
    async def insert_one(self, collection_name: str, text: str, vector: list,
                         metadata: dict = None, 
                         record_id: str = None):
        pass

    @abstractmethod
    async def insert_many(self, collection_name: str, texts: list, 
                          vectors: list, metadata: list = None, 
                          record_ids: list = None, batch_size: int = 50):
        pass

    @abstractmethod
    async def search_by_vector(self, collection_name: str, vector: list, limit: int,
                               threshold: float,
                               material_ids: Optional[List[str]] = None,
                               with_vectors: bool = False)->List[RetrievedChunk]:
        """Similarity search, optionally scoped to chunks whose stamped
        ``metadata.material_id`` is in ``material_ids`` (None = no scope).

        ``with_vectors=True`` additionally populates ``RetrievedChunk.embedding``
        (needed by MMR); callers must treat ``embedding=None`` in the results as
        "vectors unavailable" and degrade accordingly."""
        pass

    @abstractmethod
    async def delete_by_material_id(self, collection_name: str, material_id: str) -> bool:
        """Remove every chunk stamped with ``metadata.material_id`` from the
        collection, so deleting a material/file also evicts its vectors."""
        pass
    