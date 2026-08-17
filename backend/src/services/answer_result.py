"""Typed, validated output of one retrieval-backed generation."""
from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Iterable, Literal


GroundingStatus = Literal[
    "grounded", "partially_grounded", "ungrounded", "no_context"
]

_MARKER_RE = re.compile(r"\[(\d+)\]")


@dataclass(frozen=True)
class AnswerResult:
    """Internal answer contract used by chat, streaming, and evaluation."""

    text: str
    citations: list[dict[str, Any]] = field(default_factory=list)
    grounding_status: GroundingStatus = "ungrounded"
    retrieved: list[Any] = field(default_factory=list)
    latency_ms: int = 0
    time_to_first_token_ms: int | None = None

    @classmethod
    def no_context(cls, text: str, *, started_at: float | None = None) -> "AnswerResult":
        return cls(
            text=text,
            grounding_status="no_context",
            latency_ms=_elapsed_ms(started_at),
        )


def result_from_generation(
    text: str,
    retrieved: Iterable[Any],
    *,
    source_kind: str,
    started_at: float | None = None,
) -> AnswerResult:
    """Validate model markers and expose only citations it actually used.

    Unknown markers are removed from the delivered answer. A response with a
    mixture of valid and invalid markers is deliberately marked partial so the
    UI can warn the reader even though the invalid markers are hidden.
    """

    chunks = list(retrieved)
    valid_numbers = set(range(1, len(chunks) + 1))
    seen_numbers = [int(match.group(1)) for match in _MARKER_RE.finditer(text or "")]
    cited_numbers = list(dict.fromkeys(n for n in seen_numbers if n in valid_numbers))
    unknown_numbers = {n for n in seen_numbers if n not in valid_numbers}

    cleaned = _MARKER_RE.sub(
        lambda match: match.group(0)
        if int(match.group(1)) in valid_numbers
        else "",
        text or "",
    )
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)

    citations = [
        _citation_for(chunks[number - 1], number, source_kind=source_kind)
        for number in cited_numbers
    ]
    if not chunks:
        grounding: GroundingStatus = "no_context"
    elif not cited_numbers:
        grounding = "ungrounded"
    elif unknown_numbers:
        grounding = "partially_grounded"
    else:
        grounding = "grounded"

    return AnswerResult(
        text=cleaned.strip(),
        citations=citations,
        grounding_status=grounding,
        retrieved=chunks,
        latency_ms=_elapsed_ms(started_at),
    )


def _citation_for(chunk: Any, marker: int, *, source_kind: str) -> dict[str, Any]:
    metadata = getattr(chunk, "chunk_metadata", None) or {}
    page = metadata.get("page")
    slide = metadata.get("slide")
    location_type = "page" if page is not None else "slide" if slide is not None else "chunk"
    location_number = page if page is not None else slide if slide is not None else marker
    source_id = str(metadata.get("material_id") or metadata.get("source_id") or "")
    source_name = str(
        metadata.get("material_name") or metadata.get("source") or "Unknown source"
    )
    excerpt = (getattr(chunk, "chunk_text", "") or "").strip()
    return {
        "id": "cite_" + uuid.uuid4().hex[:20],
        "marker": marker,
        "sourceKind": source_kind,
        "sourceId": source_id,
        "sourceName": source_name,
        "location": {"type": location_type, "number": int(location_number)},
        "section": metadata.get("section"),
        "excerpt": excerpt[:1000],
        "score": float(getattr(chunk, "score", 0.0) or 0.0),
    }


def _elapsed_ms(started_at: float | None) -> int:
    if started_at is None:
        return 0
    return max(0, round((time.perf_counter() - started_at) * 1000))
