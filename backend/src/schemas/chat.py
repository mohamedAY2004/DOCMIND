"""Chat schemas (spec §8)."""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class CitationLocationResponse(BaseModel):
    type: Literal["page", "slide", "chunk"]
    number: int


class CitationResponse(BaseModel):
    id: str
    marker: int
    sourceKind: str
    sourceId: str
    sourceName: str
    location: CitationLocationResponse
    section: Optional[str] = None
    excerpt: str
    score: float


class MessageResponse(BaseModel):
    id: str
    role: Literal["user", "assistant", "doc"]
    text: str
    createdAt: datetime
    feedback: Optional[Literal["up", "down"]] = None
    citations: List[CitationResponse] = Field(default_factory=list)
    generationStatus: Literal["generating", "complete", "cancelled", "failed"] = "complete"
    groundingStatus: Optional[
        Literal["grounded", "partially_grounded", "ungrounded", "no_context"]
    ] = None


class ConversationResponse(BaseModel):
    id: str
    title: str
    subjectId: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime
    messageCount: int


class UpdateConversationRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)


class DocumentFileResponse(BaseModel):
    id: str
    name: str
    status: Literal["processing", "ready", "failed"]
    sizeBytes: int
    mime: str


class SendMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class CreateDocConversationResponse(BaseModel):
    conversation: ConversationResponse
    files: List[DocumentFileResponse]


class CreateTutorConversationRequest(BaseModel):
    subjectId: str


class ChatReplyResponse(BaseModel):
    userMessage: MessageResponse
    reply: MessageResponse


class LegacyReplyResponse(BaseModel):
    reply: str


class FeedbackRequest(BaseModel):
    feedback: Literal["up", "down"]
    reason: Optional[
        Literal["incorrect", "unsupported", "outdated", "unclear", "incomplete", "other"]
    ] = None
    comment: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_negative_reason(self):
        if self.feedback == "down" and self.reason is None:
            raise ValueError("A reason is required for negative feedback.")
        if self.feedback == "up" and self.reason is not None:
            raise ValueError("Positive feedback cannot include a negative reason.")
        return self


class FeedbackResponse(BaseModel):
    id: str
    messageId: str
    feedback: Literal["up", "down"]
    createdAt: datetime
    reason: Optional[str] = None
    comment: Optional[str] = None
