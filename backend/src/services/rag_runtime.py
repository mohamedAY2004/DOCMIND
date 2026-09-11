"""Compose the same retrieval policy for HTTP requests and background workers."""
from dataclasses import dataclass
from starlette.datastructures import State
from helpers.config import Settings, get_settings
from services.rag_service import RAGService
from stores.vectordb.VectorDBInterface import VectorDBInterface
from stores.llm.LLMInterface import LLMInterface
from stores.llm.templates.TemplateParser import TemplateParser
from stores.rerank.RerankInterface import RerankInterface

@dataclass(frozen=True)
class RAGRuntime:
    vectordb_client: VectorDBInterface
    embedding_client: LLMInterface
    generation_client: LLMInterface | None
    template_parser: TemplateParser | None
    rerank_client: RerankInterface | None = None

    @classmethod
    def from_state(cls, state: State) -> "RAGRuntime":
        return cls(state.vectordb_client, state.embedding_client,
                   state.generation_client, state.template_parser,
                   getattr(state, "rerank_client", None))

    def build(self, settings: Settings | None = None) -> RAGService:
        settings = settings or get_settings()
        return RAGService(
            vectordb_client=self.vectordb_client, embedding_client=self.embedding_client,
            generation_client=self.generation_client, template_parser=self.template_parser,
            rerank_client=self.rerank_client, rerank_overfetch=settings.RERANK_OVERFETCH,
            rerank_top_n=settings.RERANK_TOP_N, mmr_enabled=settings.MMR_ENABLED,
            mmr_lambda=settings.MMR_LAMBDA, mmr_overfetch=settings.MMR_OVERFETCH,
        )


def rag_from_state(state: State) -> RAGService:
    return RAGRuntime.from_state(state).build()
