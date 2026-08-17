"""Subject quality evaluation question banks, runs, and results."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin, pg_enum


class EvaluationRunStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EvaluationCase(Base, TimestampMixin):
    __tablename__ = "evaluation_cases"
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: "ec_" + uuid.uuid4().hex[:20])
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    reference_answer: Mapped[str] = mapped_column(Text, nullable=False)
    expected_material_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)


class EvaluationRun(Base, TimestampMixin):
    __tablename__ = "evaluation_runs"
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: "er_" + uuid.uuid4().hex[:20])
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[EvaluationRunStatus] = mapped_column(pg_enum(EvaluationRunStatus, name="evaluation_run_status"), nullable=False, default=EvaluationRunStatus.QUEUED)
    corpus_version: Mapped[str] = mapped_column(String(128), nullable=False)
    pipeline_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    summary_metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    failure: Mapped[Optional[str]] = mapped_column(Text)
    created_by_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)


class EvaluationResult(Base, TimestampMixin):
    __tablename__ = "evaluation_results"
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: "evr_" + uuid.uuid4().hex[:20])
    run_id: Mapped[str] = mapped_column(ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("evaluation_cases.id", ondelete="CASCADE"), nullable=False)
    generated_answer: Mapped[str] = mapped_column(Text, nullable=False, default="")
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    failure_info: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)


class GenerationTelemetry(Base, TimestampMixin):
    __tablename__ = "generation_telemetry"
    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: "gt_" + uuid.uuid4().hex[:20])
    message_id: Mapped[Optional[str]] = mapped_column(ForeignKey("messages.id", ondelete="SET NULL"), index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    subject_id: Mapped[Optional[str]] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"))
    pipeline_flags: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    retrieval_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    top_score: Mapped[Optional[float]] = mapped_column(Float)
    time_to_first_token_ms: Mapped[Optional[int]] = mapped_column(Integer)
    total_latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    completion_state: Mapped[str] = mapped_column(String(32), nullable=False)
    error_code: Mapped[Optional[str]] = mapped_column(String(64))
