"""Factory that instantiates a rerank backend based on settings.

Mirrors ``stores/agent/AgentProviderFactory.py`` and
``stores/llm/LLMProviderFactory.py`` so switching the rerank backend is a
one-line ``.env`` change::

    RERANK_BACKEND="LOCAL_CROSS_ENCODER"
"""
from __future__ import annotations

from helpers.config import Settings

from .RerankEnums import RerankBackendEnum
from .RerankInterface import RerankInterface
from .providers import CrossEncoderReranker


class RerankProviderFactory:
    def __init__(self, config: Settings):
        self.config = config

    def create(self, backend: str) -> RerankInterface:
        """Return the rerank backend matching ``backend``.

        The heavy provider dependency (sentence-transformers/torch) is imported
        lazily inside the provider, so it is only loaded when this actually
        constructs the local cross-encoder.
        """
        if backend == RerankBackendEnum.LOCAL_CROSS_ENCODER.value:
            return CrossEncoderReranker(
                model_id=self.config.RERANK_MODEL_ID,
                device=self.config.RERANK_DEVICE,
            )

        raise ValueError(f"Unsupported RERANK_BACKEND: {backend!r}")
