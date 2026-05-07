"""JSON-planner agent strategy.

Provider-agnostic: calls ``generation_client.generate_text`` twice (a
planner step that outputs a JSON decision, then a synthesis step that
produces the final answer). Works with every ``LLMInterface``
implementation today because it only relies on ``generate_text`` and
``construct_prompt`` - no native tool-calling required.

Flow:

1. Build a planner prompt that asks the LLM to output strict JSON::

       {"action": "retrieve" | "answer", "query": "<optional search query>"}

2. Parse the JSON robustly (strip ``json`` code fences, tolerate a
   surrounding paragraph). On any failure, fall back to retrieval with
   the original user query - the safer default for a RAG app.
3. If ``action == "retrieve"``: hit the vector store with the planner's
   query, then synthesise a final reply using the existing ``rag``
   template group (system / document / footer) so the output style
   matches the non-agentic path.
4. If ``action == "answer"``: synthesise directly without retrieval.
5. If retrieval returned nothing: use the ``no_context_prompt`` template
   so the model can gracefully fall back on general knowledge or
   apologise.
"""
from __future__ import annotations

import json
import logging
import re
from typing import List, Optional

from ..AgentEnums import AgentActionEnum
from ..AgentInterface import AgentInterface, AgentResult

logger = logging.getLogger("docmind.agent.json_planner")

# Match the first JSON object inside a blob of text. Non-greedy so the
# smallest balanced-looking object wins - good enough because the
# planner prompt asks for *only* JSON.
_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)
# Strip ```json ... ``` / ``` ... ``` fences if the LLM added them.
_CODE_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)


class JsonPlannerAgent(AgentInterface):
    def __init__(
        self,
        *,
        generation_client,
        template_parser,
        planner_temperature: float = 0.0,
        max_query_chars: int = 1024,
    ) -> None:
        self._generation = generation_client
        self._templates = template_parser
        self._planner_temperature = planner_temperature
        self._max_query_chars = max_query_chars

    # ---------------------- public API ----------------------

    async def answer(
        self,
        *,
        collection_name: str,
        query: str,
        rag_service,
        history: Optional[list[dict]] = None,
        subject_name: str = "",
        limit: int = 5,
        threshold: float = 0.3,
    ) -> AgentResult:
        # -------- 1. planner step --------
        decision = await self._plan(query=query, history=history, subject_name=subject_name)
        action = decision["action"]
        planner_query = decision.get("query") or query

        # -------- 2a. answer-only branch --------
        if action == AgentActionEnum.ANSWER.value:
            text = await self._generate_direct(query=query, history=history, subject_name=subject_name)
            return AgentResult(
                text=text or "",
                used_retrieval=False,
                planner_query=None,
                retrieved=[],
            )

        # -------- 2b. retrieval branch --------
        retrieved = await rag_service.search(
            collection_name,
            planner_query,
            limit=limit,
            threshold=threshold,
        )

        if not retrieved:
            text = await self._generate_no_context(query=query, history=history, subject_name=subject_name)
            return AgentResult(
                text=text or "",
                used_retrieval=True,
                planner_query=planner_query,
                retrieved=[],
            )

        text = await self._synthesize_with_context(
            query=query, chunks=retrieved, history=history, subject_name=subject_name
        )
        return AgentResult(
            text=text or "",
            used_retrieval=True,
            planner_query=planner_query,
            retrieved=list(retrieved),
        )

    # ---------------------- planner ----------------------

    async def _plan(
        self, *, query: str, history: Optional[list[dict]], subject_name: str = ""
    ) -> dict:
        planner_prompt = self._templates.get(
            group="agent",
            key="planner_prompt",
            variables={
                "query": query,
                "history": _render_history(history),
                "subject_name": subject_name,
            },
        )
        if not planner_prompt:
            # Template missing - safest default is to retrieve.
            logger.warning(
                "agent.planner_prompt template missing; defaulting to retrieve"
            )
            return {
                "action": AgentActionEnum.RETRIEVE.value,
                "query": query,
            }

        chat_history = [
            self._generation.construct_prompt(
                prompt=planner_prompt,
                role=self._generation.enums.SYSTEM.value,
            )
        ]
        raw = await self._generation.generate_text_async(
            prompt="Return the JSON now.",
            chat_history=chat_history,
            temperature=self._planner_temperature,
        )
        return _parse_planner_json(raw, fallback_query=query)

    # ---------------------- synthesis variants ----------------------

    async def _synthesize_with_context(
        self,
        *,
        query: str,
        chunks: List,
        history: Optional[list[dict]],
        subject_name: str = "",
    ) -> str:
        # Reuse the existing 'rag' template group so the final reply
        # has identical shape to the non-agentic path.
        system_prompt = self._templates.get(
            group="rag", key="system_prompt",
            variables={"subject_name": subject_name},
        )
        docs_block = "\n".join(
            self._templates.get(
                group="rag",
                key="document_prompt",
                variables={
                    "doc_num": i + 1,
                    "chunk_text": getattr(c, "chunk_text", ""),
                },
            )
            for i, c in enumerate(chunks)
        )
        footer = self._templates.get(group="rag", key="footer_prompt")

        chat_history = self._build_chat_history(
            system_prompt=system_prompt, history=history
        )

        full_prompt = "\n\n".join([docs_block, footer, query])
        reply = await self._generation.generate_text_async(
            prompt=full_prompt, chat_history=chat_history
        )
        return reply or ""

    async def _generate_direct(
        self, *, query: str, history: Optional[list[dict]], subject_name: str = ""
    ) -> str:
        system_prompt = (
            self._templates.get(
                group="agent", key="direct_answer_prompt",
                variables={"subject_name": subject_name},
            )
            or "You are a helpful academic assistant. Answer concisely."
        )
        chat_history = self._build_chat_history(
            system_prompt=system_prompt, history=history
        )
        reply = await self._generation.generate_text_async(
            prompt=query, chat_history=chat_history
        )
        return reply or ""

    async def _generate_no_context(
        self, *, query: str, history: Optional[list[dict]], subject_name: str = ""
    ) -> str:
        system_prompt = (
            self._templates.get(
                group="agent", key="no_context_prompt",
                variables={"subject_name": subject_name},
            )
            or (
                "No relevant documents were found. Answer from general "
                "knowledge if you can; otherwise politely say you do not "
                "have enough information."
            )
        )
        chat_history = self._build_chat_history(
            system_prompt=system_prompt, history=history
        )
        reply = await self._generation.generate_text_async(
            prompt=query, chat_history=chat_history
        )
        return reply or ""

    # ---------------------- provider-aware history plumbing ----------------------

    def _build_chat_history(
        self,
        *,
        system_prompt: str,
        history: Optional[list[dict]],
    ) -> list:
        """Construct a ``chat_history`` list in the current provider's schema.

        Each incoming ``history`` entry is a generic
        ``{"role": "user"|"assistant"|..., "content": "..."}`` dict. We
        translate the role to the provider's own enum (so Gemini gets
        ``"model"`` instead of ``"assistant"``, etc.) and re-wrap via
        ``construct_prompt`` so Gemini gets a ``types.Content`` while
        OpenAI/Cohere get the right dict shape.
        """
        chat_history: list = [
            self._generation.construct_prompt(
                prompt=system_prompt,
                role=self._generation.enums.SYSTEM.value,
            )
        ]
        if not history:
            return chat_history

        enums = self._generation.enums
        for msg in history:
            content = _content_of(msg)
            if not content:
                continue
            generic_role = _role_of(msg)
            if generic_role == "assistant":
                role = enums.ASSISTANT.value
            elif generic_role == "system":
                role = enums.SYSTEM.value
            else:
                role = enums.USER.value
            chat_history.append(
                self._generation.construct_prompt(prompt=content, role=role)
            )
        return chat_history


# ---------------------- helpers (module-level) ----------------------


def _render_history(history: Optional[list[dict]]) -> str:
    """Render chat history into a compact plain-text block for the planner.

    The planner only reads this for *decision-making*; the actual
    conversational history is still injected into synthesis calls via
    ``chat_history``. Keeping a text version avoids coupling the planner
    prompt to any provider's message schema.
    """
    if not history:
        return "(no prior messages)"
    lines: List[str] = []
    for msg in history[-8:]:  # last 8 turns is plenty for a planning hint
        role = _role_of(msg)
        content = _content_of(msg)
        if not content:
            continue
        lines.append(f"{role}: {content}")
    return "\n".join(lines) if lines else "(no prior messages)"


def _role_of(msg: dict) -> str:
    role = msg.get("role") or "user"
    role = str(role).lower()
    if role in {"model", "chatbot", "assistant", "doc"}:
        return "assistant"
    if role == "system":
        return "system"
    return "user"


def _content_of(msg: dict) -> str:
    # OpenAI-style dicts use 'content'; Cohere-style use 'text'.
    for key in ("content", "text", "message"):
        val = msg.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _parse_planner_json(raw: Optional[str], *, fallback_query: str) -> dict:
    """Parse the planner output into ``{"action", "query"}``.

    Falls back to retrieval with the original user query on any failure -
    that's the safer default for a RAG app (better to retrieve
    unnecessarily than to hallucinate without context).
    """
    default = {
        "action": AgentActionEnum.RETRIEVE.value,
        "query": fallback_query,
    }
    if not raw:
        logger.warning("Planner returned empty response; defaulting to retrieve")
        return default

    cleaned = _CODE_FENCE_RE.sub("", raw.strip())
    match = _JSON_OBJECT_RE.search(cleaned)
    if not match:
        logger.warning("Planner output contained no JSON object: %r", raw[:200])
        return default

    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        logger.warning("Planner output was not valid JSON: %r", raw[:200])
        return default

    action = str(data.get("action", "")).lower().strip()
    if action not in {
        AgentActionEnum.RETRIEVE.value,
        AgentActionEnum.ANSWER.value,
    }:
        logger.warning("Planner returned unknown action %r; defaulting to retrieve", action)
        return default

    query = data.get("query")
    if not isinstance(query, str) or not query.strip():
        query = fallback_query
    return {"action": action, "query": query.strip()}
