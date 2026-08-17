"""Prompt-free generation telemetry and lightweight operational counters."""
from __future__ import annotations

from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import GenerationTelemetry
from helpers.config import get_settings


class MetricsRegistry:
    def __init__(self) -> None:
        self.counters: dict[str, float] = defaultdict(float)
        self.sums: dict[str, float] = defaultdict(float)
        self.counts: dict[str, int] = defaultdict(int)
        self.gauges: dict[str, float] = {}

    def increment(self, name: str, value: float = 1) -> None:
        self.counters[name] += value

    def observe(self, name: str, value: float) -> None:
        self.sums[name] += value
        self.counts[name] += 1

    def set_gauge(self, name: str, value: float) -> None:
        self.gauges[name] = value

    def render(self) -> str:
        lines: list[str] = []
        for name, value in sorted(self.counters.items()):
            lines.append(f"docmind_{name} {value}")
        for name, value in sorted(self.gauges.items()):
            lines.append(f"docmind_{name} {value}")
        for name, value in sorted(self.sums.items()):
            lines.append(f"docmind_{name}_sum {value}")
            lines.append(f"docmind_{name}_count {self.counts[name]}")
        return "\n".join(lines) + "\n"


metrics = MetricsRegistry()


class TelemetryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, *, message_id: str | None, subject_id: str | None, result=None, state: str, error_code: str | None = None) -> None:
        settings = get_settings()
        retrieved = list(getattr(result, "retrieved", []) or [])
        self._session.add(GenerationTelemetry(
            message_id=message_id,
            provider=settings.GENERATION_BACKEND,
            model=settings.GENERATION_MODEL_ID or "unknown",
            subject_id=subject_id,
            pipeline_flags={"agent": settings.AGENT_ENABLED, "rerank": settings.RERANK_ENABLED, "mmr": settings.MMR_ENABLED},
            retrieval_count=len(retrieved),
            top_score=max((float(getattr(item, "score", 0) or 0) for item in retrieved), default=None),
            time_to_first_token_ms=getattr(result, "time_to_first_token_ms", None),
            total_latency_ms=getattr(result, "latency_ms", None),
            completion_state=state,
            error_code=error_code,
        ))
        if result is not None:
            metrics.observe("generation_total_latency_ms", getattr(result, "latency_ms", 0) or 0)
            if getattr(result, "time_to_first_token_ms", None) is not None:
                metrics.observe("generation_ttft_ms", result.time_to_first_token_ms)
            if getattr(result, "grounding_status", None) == "no_context":
                metrics.increment("generation_no_context_total")
            metrics.increment("citation_answers_total")
            if getattr(result, "citations", None):
                metrics.increment("citation_answers_with_citations_total")
        metrics.increment(f"generation_{state}_total")
