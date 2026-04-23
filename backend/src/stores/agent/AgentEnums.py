"""Enums for the agentic RAG layer.

Kept in the same shape as ``stores/llm/LLMEnums.py`` and
``stores/vectordb/VectorDBEnums.py`` so the agent component follows the
exact factory + enums + ``.env`` pattern used elsewhere.
"""
from enum import Enum


class AgentStrategyEnum(Enum):
    """Pluggable agent strategies.

    Add a new value here and a matching class under ``strategies/`` +
    ``AgentProviderFactory.create`` to introduce a new strategy
    (e.g. native tool-calling). Selection is driven from ``AGENT_STRATEGY``
    in the ``.env`` file.
    """

    JSON_PLANNER = "JSON_PLANNER"


class AgentActionEnum(Enum):
    """Actions the JSON planner may emit."""

    RETRIEVE = "retrieve"
    ANSWER = "answer"
