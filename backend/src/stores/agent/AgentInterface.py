"""Abstract agent interface.

An agent wraps the decision of *whether* to retrieve and *with what query*
around the existing ``RAGService`` + ``LLMInterface`` primitives. Concrete
strategies live under ``stores/agent/strategies`` and are built by
``AgentProviderFactory``.

The interface is deliberately thin so alternative strategies (e.g. native
tool-calling) can slot in without touching callers.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AgentResult:
    """The outcome of one agent turn.

    Attributes:
        text: Final assistant reply to show the user.
        used_retrieval: Whether the agent chose to call the vector store.
        planner_query: The query the planner decided to retrieve with
            (``None`` when ``used_retrieval`` is False).
        retrieved: The raw retrieved chunks, kept for logging / tracing.
        sources_filter: The ``material_id``s retrieval was scoped to (empty
            when the search covered the whole subject).
    """

    text: str
    used_retrieval: bool = False
    planner_query: Optional[str] = None
    retrieved: List = field(default_factory=list)
    sources_filter: List[str] = field(default_factory=list)


class AgentInterface(ABC):
    """Contract every agent strategy must honour."""

    @abstractmethod
    async def answer(
        self,
        *,
        collection_name: str,
        query: str,
        rag_service,
        history: Optional[list[dict]] = None,
        subject_name: str = "",
        subject_manifest: str = "",
        material_index: Optional[list[tuple[str, str]]] = None,
        source_filter_enabled: bool = False,
        limit: int = 5,
        threshold: float = 0.3,
    ) -> AgentResult:
        """Produce an answer for ``query`` against ``collection_name``.

        ``rag_service`` is passed per-call because it is constructed
        per-request in the routes (it is a thin wrapper around the
        app-level singletons).

        ``history`` is an optional list of ``{"role": "...", "content": "..."}``
        dicts representing the recent conversation, used by the planner
        to decide whether retrieval is needed.

        ``subject_name`` is the human-readable name of the subject (e.g.
        "CS201 — Data Structures") used to scope the agent's answers so
        it refuses questions outside that subject.

        ``subject_manifest`` is a short, pre-rendered list of the subject's
        indexed materials so the planner/synthesis steps know which
        documents are actually available to ground answers in.

        ``material_index`` is the ``(material_id, name)`` allowlist used to
        validate and resolve any material names the planner chooses to scope
        retrieval to. ``source_filter_enabled`` gates that behaviour; when
        false the agent always searches the whole subject collection.
        """
        raise NotImplementedError
