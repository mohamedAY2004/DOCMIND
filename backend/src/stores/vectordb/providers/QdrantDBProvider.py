from qdrant_client import models, AsyncQdrantClient
from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnum
from typing import List
import logging
import uuid
from models.db_schemes import RetrievedChunk
class QdrantDBProvider(VectorDBInterface):
    def __init__(self, db_path: str, distance_method: str):
        self.client = None
        self.db_path = db_path
        self.distance_method = None
        self.logger = logging.getLogger(__name__)
        if distance_method == DistanceMethodEnum.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMethodEnum.DOT.value:
            self.distance_method = models.Distance.DOT
        elif distance_method == DistanceMethodEnum.EUCLID.value:
            self.distance_method = models.Distance.EUCLID
        elif distance_method == DistanceMethodEnum.MANHATTAN.value:
            self.distance_method = models.Distance.MANHATTAN
        else:
            self.logger.error(f"Invalid distance method: {distance_method}")

    async def connect(self):
        self.client = AsyncQdrantClient(path=self.db_path)
    async def disconnect(self):
        if self.client :
            await self.client.close()
            self.client=None

    async def is_collection_exists(self, collection_name: str)->bool:
        return await self.client.collection_exists(collection_name)

    async def list_all_collections(self) -> List:
        return await self.client.get_collections()

    async def get_collection_info(self, collection_name: str) -> dict:
        return await self.client.get_collection(collection_name)

    async def delete_collection(self, collection_name: str):
        if await self.is_collection_exists(collection_name):
            return await self.client.delete_collection(collection_name)
        return False

    async def create_collection(self, collection_name: str, 
                                embedding_size: int,
                                do_reset: bool = False)->bool:
        if do_reset:
           await self.delete_collection(collection_name) 
        if not await self.is_collection_exists(collection_name):
            return await self.client.create_collection(collection_name,
             vectors_config=models.VectorParams(size=embedding_size, distance=self.distance_method),
             optimizers_config=models.OptimizersConfigDiff(indexing_threshold=0)  # force immediate indexing
            )
        return False

    async def insert_one(self, collection_name: str, text: str, vector: list,
                         metadata: dict = None, 
                         record_id: str = None):
        if not await self.is_collection_exists(collection_name):
            self.logger.error(f"Collection {collection_name} does not exist to insert record")
            return False
        try:
            _=await self.client.upsert(collection_name=collection_name,points=[models.PointStruct(id=self._to_qdrant_id(record_id), vector=vector, payload={"metadata": metadata, "text": text})])
        except Exception as e:
            self.logger.error(f"Error inserting record into collection {collection_name}: {e}")
            return False
        return True
    async def insert_many(self, collection_name: str, texts: list, 
                          vectors: list, metadata: list = None, 
                          record_ids: list = None, batch_size: int = 50):
        if metadata is None:
            metadata = [None] * len(texts)
        if record_ids is None:
            self.logger.error(f"Record IDs are required to insert records")
            return False
        if not self.client:
            self.logger.error(f"Client is not connected to the database")
            return False
        if not await self.is_collection_exists(collection_name):
            self.logger.error(f"Collection {collection_name} does not exist to insert records")
            return False
        if len(texts) != len(vectors) or len(texts) != len(metadata) or len(texts) != len(record_ids):
            self.logger.error(f"Length of texts, vectors, metadata, and record_ids must be the same")
            return False
        for i in range(0, len(texts), batch_size):
            batch_end=min(i+batch_size, len(texts))
            batch_records = [
                models.PointStruct(id=self._to_qdrant_id(record_ids[x]), vector=vectors[x], payload={"metadata": metadata[x], "text": texts[x]})
                 for x in  range(i,batch_end)
                ]
            try:
                _=await self.client.upsert(collection_name,points=batch_records)
            except Exception as e:
                self.logger.error(f"Error inserting batch of records into collection {collection_name}: {e}")
                return False
        return True


    async def search_by_vector(self, collection_name: str, vector: list, limit: int,threshold: float = 0.5)->List[RetrievedChunk]:
        if not await self.is_collection_exists(collection_name):
            self.logger.error(f"Collection {collection_name} does not exist to search records") 
            return None
        results = await self.client.query_points(collection_name=collection_name, query=vector, limit=limit, with_payload=True,score_threshold=threshold)
        if results:
            return [RetrievedChunk(chunk_text=result.payload["text"], score=result.score, chunk_metadata=result.payload["metadata"]) for result in results.points]
        else:
            return None

    def _to_qdrant_id(self, record_id) -> str:
        hex_str = str(record_id).zfill(32)
        return str(uuid.UUID(hex_str))