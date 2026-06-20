"""Enums for the reranking layer.

Kept in the same shape as ``stores/agent/AgentEnums.py`` and
``stores/llm/LLMEnums.py`` so the reranker follows the exact factory + enums +
``.env`` pattern used elsewhere. Selection is driven from ``RERANK_BACKEND``.
"""
from enum import Enum


class RerankBackendEnum(Enum):
    """Pluggable rerank backends.

    Add a new value here and a matching provider under ``providers/`` +
    ``RerankProviderFactory.create`` to introduce a new backend (e.g. a managed
    rerank API). Only the local cross-encoder ships today.
    """

    LOCAL_CROSS_ENCODER = "LOCAL_CROSS_ENCODER"
