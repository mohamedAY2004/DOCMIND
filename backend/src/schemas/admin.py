"""Admin schemas (spec §10)."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class SubjectStatsResponse(BaseModel):
    id: str
    title: str
    semester: Optional[str] = None
    pdfCount: int
    materialStatus: Literal["indexing", "processed", "mixed", "empty"]
    interactions: int
    aiResponses: int
    thumbsUp: int
    thumbsDown: int
    instructorIds: List[str] = Field(default_factory=list)
    superInstructorId: Optional[str] = None


class FeedbackRowResponse(BaseModel):
    id: str
    student: str
    studentId: str
    subject: str
    subjectId: str
    semester: Optional[str] = None
    question: str
    aiResponse: str
    feedback: Literal["up", "down"]
    timestamp: datetime


class ActivityResponse(BaseModel):
    id: str
    action: str
    user: Optional[str] = None
    time: datetime


class DailyUsageResponse(BaseModel):
    day: date
    conversations: int
    questions: int
