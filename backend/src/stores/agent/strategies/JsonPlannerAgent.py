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
        subject_manifest: str = "",
        material_index: Optional[list[tuple[str, str]]] = None,
        source_filter_enabled: bool = False,
        limit: int = 5,
        threshold: float = 0.3,
    ) -> AgentResult:
        # -------- 1. planner step --------
        decision = await self._plan(
            query=query,
            history=history,
            subject_name=subject_name,
            subject_manifest=subject_manifest,
        )
        action = decision["action"]
        planner_query = decision.get("query") or query

        # -------- 2a. answer-only branch --------
        if action == AgentActionEnum.ANSWER.value:
            text = await self._generate_direct(
                query=query,
                history=history,
                subject_name=subject_name,
                subject_manifest=subject_manifest,
            )
            return AgentResult(
                text=text or "",
                used_retrieval=False,
                planner_query=None,
                retrieved=[],
            )

        # -------- 2b. retrieval branch --------
        # Resolve any planner-chosen source names to known material ids. Unknown
        # names (hallucinations) are dropped; an empty result means no scope.
        material_ids = self._resolve_sources(
            decision.get("sources"),
            material_index=material_index,
            enabled=source_filter_enabled,
        )

        retrieved = await rag_service.search(
            collection_name,
            planner_query,
            limit=limit,
            threshold=threshold,
            material_ids=material_ids or None,
        )

        # Bounded fallback: if scoping to specific materials found nothing (e.g.
        # the planner picked the wrong doc), retry once over the whole subject
        # before giving up. Caps the extra cost at one more vector query.
        applied_filter = list(material_ids)
        if not retrieved and material_ids:
            logger.info(
                "agent.source_filter empty for ids=%s; retrying unfiltered",
                material_ids,
            )
            applied_filter = []
            retrieved = await rag_service.search(
                collection_name,
                planner_query,
                limit=limit,
                threshold=threshold,
                material_ids=None,
            )

        if not retrieved:
            text = await self._generate_no_context(
                query=query,
                history=history,
                subject_name=subject_name,
                subject_manifest=subject_manifest,
            )
            return AgentResult(
                text=text or "",
                used_retrieval=True,
                planner_query=planner_query,
                retrieved=[],
                sources_filter=applied_filter,
            )

        text = await self._synthesize_with_context(
            query=query,
            chunks=retrieved,
            history=history,
            subject_name=subject_name,
            subject_manifest=subject_manifest,
            rag_service=rag_service,
        )
        return AgentResult(
            text=text or "",
            used_retrieval=True,
            planner_query=planner_query,
            retrieved=list(retrieved),
            sources_filter=applied_filter,
        )

    @staticmethod
    def _resolve_sources(
        sources,
        *,
        material_index: Optional[list[tuple[str, str]]],
        enabled: bool,
    ) -> list[str]:
        """Map planner-chosen material *names* to known material *ids*.

        Returns ``[]`` (no scope) when the feature is off, nothing was chosen,
        or none of the chosen names match the subject's allowlist.
        """
        if not enabled or not sources or not material_index:
            return []
        name_to_id = {name: mid for (mid, name) in material_index}
        ids = [name_to_id[name] for name in sources if name in name_to_id]
        # Preserve order, drop duplicates.
        return list(dict.fromkeys(ids))

    # ---------------------- planner ----------------------

    async def _plan(
        self,
        *,
        query: str,
        history: Optional[list[dict]],
        subject_name: str = "",
        subject_manifest: str = "",
    ) -> dict:
        planner_prompt = self._templates.get(
            group="agent",
            key="planner_prompt",
            variables={
                "query": query,
                "history": _render_history(history),
                "subject_name": subject_name,
                "subject_manifest": subject_manifest,
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
        subject_manifest: str = "",
        rag_service,
    ) -> str:
        # Reuse the RAGService prompt builders so the final reply has an
        # identical, source-attributed shape to the non-agentic path.
        system_prompt = rag_service.build_system_prompt(subject_name, subject_manifest)
        docs_block = rag_service.build_docs_block(chunks)
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
        self,
        *,
        query: str,
        history: Optional[list[dict]],
        subject_name: str = "",
        subject_manifest: str = "",
    ) -> str:
        system_prompt = (
            self._templates.get(
                group="agent", key="direct_answer_prompt",
                variables={
                    "subject_name": subject_name,
                    "subject_manifest": subject_manifest,
                },
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
        self,
        *,
        query: str,
        history: Optional[list[dict]],
        subject_name: str = "",
        subject_manifest: str = "",
    ) -> str:
        system_prompt = (
            self._templates.get(
                group="agent", key="no_context_prompt",
                variables={
                    "subject_name": subject_name,
                    "subject_manifest": subject_manifest,
                },
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


def _coerce_sources(value) -> list[str]:
    """Normalise the optional planner ``sources`` field to a list of strings.

    Tolerates a bare string (wrap), a list (filter to non-empty strings), or
    anything else (ignore). Names are validated against the allowlist later.
    """
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [v.strip() for v in value if isinstance(v, str) and v.strip()]
    return []


def _parse_planner_json(raw: Optional[str], *, fallback_query: str) -> dict:
    """Parse the planner output into ``{"action", "query", "sources"}``.

    Falls back to retrieval with the original user query on any failure -
    that's the safer default for a RAG app (better to retrieve
    unnecessarily than to hallucinate without context).
    """
    default = {
        "action": AgentActionEnum.RETRIEVE.value,
        "query": fallback_query,
        "sources": [],
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
    return {
        "action": action,
        "query": query.strip(),
        "sources": _coerce_sources(data.get("sources")),
    }
