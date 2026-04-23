from stores.llm import LLMEnums
from .BaseController import BaseController
from models.db_schemes import Project, DataChunk
from stores.llm.LLMEnums import DocumentTypeEnum
from typing import List
import logging
import json
class NLPController(BaseController):
    def __init__(self, vectordb_client, generation_client, embedding_client,template_parser):
        super().__init__()
        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser
        self.logger = logging.getLogger(__name__)
    def create_collection_name(self, project_id: str):
        return f"collection_{project_id}".strip().lower()
    async def reset_vectordb_collection(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        await self.vectordb_client.delete_collection(collection_name=collection_name)
    
    async def get_vectordb_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        info = await self.vectordb_client.get_collection_info(collection_name=collection_name)
        return json.loads(
            json.dumps(info,default=lambda x: x.__dict__)
        )
    async def index_into_vectordb(self, project: Project, chunks: List[DataChunk], do_reset: bool = False):
        
        #step 1: get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)
        
        
        #step 2: manage items to index
        texts = [c.chunk_text for c in chunks]
        metadata = [c.chunk_metadata for c in chunks]
        record_ids = [c.id for c in chunks]
        vectors = [
            self.embedding_client.embed_text(text=text,document_type=DocumentTypeEnum.DOCUMENT.value)[0] 
            for text in texts
        ]
        
        
        #step 3: create collection if not exists
        await self.vectordb_client.create_collection(collection_name=collection_name, embedding_size=self.embedding_client.embedding_size, do_reset=do_reset)
        
        
        #step 4: index items into collection
        await self.vectordb_client.insert_many(collection_name=collection_name, texts=texts, vectors=vectors, metadata=metadata, record_ids=record_ids)
        return True
    
    async def search_vectordb(self, project: Project, query: str,limit: int = 5,threshold: float=0.5):
        #get collection name
        collection_name= self.create_collection_name(project_id=project.project_id)
        # get embedding
        vector= self.embedding_client.embed_text(text= query, document_type=LLMEnums.DocumentTypeEnum.QUERY.value)
        if len(vector)==0:
            self.logger.error("Failed to embed query at search_vectordb NLPController")
            return False
        else:
            vector=vector[0]
        # do semantic search
        results = await self.vectordb_client.search_by_vector(collection_name=collection_name, vector=vector, limit=limit,threshold=threshold)

        if not results:
            return None

        return results
    
    async def answer_rag_question(self, project: Project, query: str,limit: int = 5,threshold: float=0.5):
        #step 1: retrive
        retrived_chunks=await self.search_vectordb(project=project,query=query,limit=limit,threshold=threshold)
        if not retrived_chunks or len(retrived_chunks)==0:
            return None

        #step 2:construct LLM prompt
        system_prompt=self.template_parser.get(group="rag",key="system_prompt")

        # document_prompts=[]
        # for i,chunk in enumerate(retrived_chunks):
        #     document_prompts.append(self.template_parser.get(group="rag",key="document_prompt",variables={"doc_num": i+1, "chunk_text": chunk.chunk_text}))

        document_prompts ="\n".join([
            self.template_parser.get(group="rag",key="document_prompt",variables={"doc_num": i+1, "chunk_text": chunk.chunk_text})
            for i,chunk in enumerate(retrived_chunks)
        ])

        footer_prompt=self.template_parser.get(group="rag",key="footer_prompt")

        chat_history=[
            self.generation_client.construct_prompt(prompt=system_prompt, role=self.generation_client.enums.SYSTEM.value)
        ]

        full_prompt="\n\n".join([document_prompts,footer_prompt,query])
        answer= self.generation_client.generate_text(prompt=full_prompt, chat_history=chat_history)
        
        return answer

