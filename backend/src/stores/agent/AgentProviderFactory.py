"""Factory that instantiates an agent strategy based on settings.

Mirrors ``stores/llm/LLMProviderFactory.py`` and
``stores/vectordb/VectorDBProviderFactory.py`` so switching the agent
strategy is a one-line ``.env`` change:

    AGENT_STRATEGY="JSON_PLANNER"
"""
from __future__ import annotations

from helpers.config import Settings

from .AgentEnums import AgentStrategyEnum
from .AgentInterface import AgentInterface
from .strategies import JsonPlannerAgent


class AgentProviderFactory:
    def __init__(self, config: Settings):
        self.config = config

    def create(
        self,
        strategy: str,
        *,
        generation_client,
        template_parser,
    ) -> AgentInterface:
        """Return the strategy implementation matching ``strategy``.

        ``generation_client`` and ``template_parser`` are the app-level
        singletons built by ``LLMProviderFactory`` at startup.
        """
        if strategy == AgentStrategyEnum.JSON_PLANNER.value:
            return JsonPlannerAgent(
                generation_client=generation_client,
                template_parser=template_parser,
                planner_temperature=self.config.AGENT_PLANNER_TEMPERATURE,
                max_query_chars=self.config.DEFAULT_INPUT_MAX_CHARACTERS or 1024,
            )

        raise ValueError(f"Unsupported AGENT_STRATEGY: {strategy!r}")
