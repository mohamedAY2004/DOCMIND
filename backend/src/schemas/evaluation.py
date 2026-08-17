from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class EvaluationCaseRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    referenceAnswer: str = Field(..., min_length=1, max_length=12000)
    expectedMaterialIds: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    active: bool = True


class FeedbackEvaluationCaseRequest(BaseModel):
    referenceAnswer: str = Field(..., min_length=1, max_length=12000)
    expectedMaterialIds: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class EvaluationCaseResponse(EvaluationCaseRequest):
    id: str
    subjectId: str
    createdBy: str
    createdAt: datetime
    updatedAt: datetime


class EvaluationRunResponse(BaseModel):
    id: str
    subjectId: str
    status: str
    corpusVersion: str
    pipelineSnapshot: dict[str, Any]
    summaryMetrics: dict[str, Any]
    failure: Optional[str] = None
    createdAt: datetime
    startedAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None


class EvaluationResultResponse(BaseModel):
    id: str
    runId: str
    caseId: str
    generatedAnswer: str
    citations: list[dict[str, Any]]
    metrics: dict[str, Any]
    failureInfo: Optional[dict[str, Any]] = None


class ReadinessResponse(BaseModel):
    subjectId: str
    state: str
    reasons: list[str]
    activeCases: int
    processedMaterials: int
    failedMaterials: int
    latestRunId: Optional[str] = None
    metrics: dict[str, Any] = Field(default_factory=dict)
