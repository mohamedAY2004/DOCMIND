"""Chat schemas (spec §8)."""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    id: str
    role: Literal["user", "assistant", "doc"]
    text: str
    createdAt: datetime
    feedback: Optional[Literal["up", "down"]] = None


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


class FeedbackResponse(BaseModel):
    id: str
    messageId: str
    feedback: Literal["up", "down"]
    createdAt: datetime
