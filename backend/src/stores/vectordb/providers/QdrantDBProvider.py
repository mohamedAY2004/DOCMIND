from qdrant_client import models, AsyncQdrantClient
from ..VectorDBInterface import VectorDBInterface
from ..errors import VectorStoreError, vector_write, validate_batch
from ..VectorDBEnums import DistanceMethodEnum
from typing import List, Optional
import logging
import uuid
from stores.vectordb.types import RetrievedChunk
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
            raise ValueError(f"Unsupported vector distance method: {distance_method}")

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
            # Validate every PointStruct before starting a potentially partial remote write.
            points = [models.PointStruct(id=self._to_qdrant_id(record_ids[i]), vector=vector,
                       payload={"metadata": metadata[i], "text": texts[i]}) for i, vector in enumerate(vectors)]
            for start in range(0, len(points), batch_size):
                result = await self.client.upsert(collection_name=collection_name,
                    points=points[start:start + batch_size], wait=True)
                if result.status != models.UpdateStatus.COMPLETED:
                    raise VectorStoreError("Qdrant did not confirm completed persistence")

    async def delete_by_material_id(self, collection_name: str, material_id: str) -> bool:
        if not await self.is_collection_exists(collection_name):
            return False
        await self.client.delete(
            collection_name=collection_name,
            wait=True,
            points_selector=models.FilterSelector(filter=models.Filter(must=[
                models.FieldCondition(
                    key="metadata.material_id",
                    match=models.MatchValue(value=material_id),
                )
            ])),
        )
        return True

    async def search_by_vector(self, collection_name: str, vector: list, limit: int,threshold: float = 0.5,
                               material_ids: Optional[List[str]] = None,
                               with_vectors: bool = False)->List[RetrievedChunk]:
        if not await self.is_collection_exists(collection_name):
            self.logger.error(f"Collection {collection_name} does not exist to search records")
            return None
        # Optionally scope to specific owning materials (None = no scope, so the
        # unscoped path is unchanged). Keys off the metadata stamped at index time.
        query_filter = None
        if material_ids:
            query_filter = models.Filter(must=[
                models.FieldCondition(
                    key="metadata.material_id",
                    match=models.MatchAny(any=list(material_ids)),
                )
            ])
        results = await self.client.query_points(collection_name=collection_name, query=vector, limit=limit, with_payload=True,score_threshold=threshold, query_filter=query_filter, with_vectors=with_vectors)
        if results:
            return [
                RetrievedChunk(
                    chunk_text=result.payload["text"],
                    score=result.score,
                    chunk_metadata=result.payload.get("metadata") or {},
                    embedding=self._point_vector(result) if with_vectors else None,
                )
                for result in results.points
            ]
        else:
            return None

    @staticmethod
    def _point_vector(point) -> Optional[list]:
        vec = getattr(point, "vector", None)
        if isinstance(vec, dict):  # named-vector collections
            vec = next(iter(vec.values()), None)
        return list(vec) if vec is not None else None

    def _to_qdrant_id(self, record_id) -> str:
        try:
            return str(uuid.UUID(str(record_id)))
        except ValueError:
            return str(uuid.uuid5(uuid.NAMESPACE_URL, "docmind:" + str(record_id)))
