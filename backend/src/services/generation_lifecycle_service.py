"""Persistence and cancellation state machine shared by document and tutor turns."""
from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from db.models import Conversation, Message, MessageRole, GenerationStatus, GroundingStatus
from helpers.config import get_settings
from repositories.message_repository import MessageRepository
from schemas.chat import MessageResponse, ChatReplyResponse
from helpers.errors import APIError, ErrorCode
from services.answer_result import AnswerResult, result_from_generation
from services.generation_control import GenerationCancelled, await_cancellable, iter_cancellable
from services.generation_source import generate_answer
from services.telemetry_service import TelemetryService

logger = logging.getLogger("docmind.generation")

@dataclass(frozen=True)
class PreparedChatTurn:
    conversation: Conversation
    text: str
    collection: str
    reply_role: MessageRole
    source_kind: str
    history: list[dict] | None = None
    subject_name: str = ""
    subject_manifest: str = ""
    material_index: list[tuple[str, str]] = field(default_factory=list)

class GenerationLifecycleService:
    def __init__(self, session):
        self._session = session
        self._messages = MessageRepository(session)

    async def reply(self, turn: PreparedChatTurn, rag, agent) -> ChatReplyResponse:
        user_message, reply = None, None
        async for event, payload in self.stream(turn, rag, agent, None, streaming=False):
            if event == "message.created":
                user_message = payload["userMessage"]
            elif event == "answer.completed":
                reply = payload["reply"]
            elif event == "answer.failed":
                raise APIError(ErrorCode.INTERNAL_ERROR, 500, "Generation failed.")
        if user_message is None or reply is None:
            raise APIError(ErrorCode.INTERNAL_ERROR, 500, "Generation ended without a reply.")
        return ChatReplyResponse(userMessage=user_message, reply=reply)

    async def stream(self, turn: PreparedChatTurn, rag, agent, store, *, streaming=True):
        conv, text = turn.conversation, turn.text
        subject_id = conv.subject_id
        subject_name, subject_manifest = turn.subject_name, turn.subject_manifest
        material_index, history = turn.material_index, turn.history

        user_msg = await self._messages.add(
            Message(conversation_id=conv.id, role=MessageRole.USER, text=text)
        )
        reply = await self._messages.add(
            Message(
                conversation_id=conv.id,
                role=turn.reply_role,
                text="",
                generation_status=GenerationStatus.GENERATING,
            )
        )
        conv.updated_at = datetime.now(timezone.utc)
        await self._session.commit()
        result: AnswerResult | None = None
        try:
            yield "message.created", {
                "userMessage": _message_response(user_msg).model_dump(mode="json"),
                "reply": _message_response(reply).model_dump(mode="json"),
            }
            source = generate_answer(rag, agent, collection=turn.collection, text=text,
                                     source_kind=turn.source_kind, history=history,
                                     subject_name=subject_name, subject_manifest=subject_manifest,
                                     material_index=material_index, streaming=streaming)
            events = iter_cancellable(source, store=store, reply_id=reply.id) if store else source
            async for kind, payload in events:
                if kind == "delta":
                    yield "answer.delta", {"replyId": reply.id, "delta": payload}
                else:
                    result = payload
            if result is None:
                raise RuntimeError("Generation completed without a result")
            completed = await self._messages.complete_if_generating(
                reply.id,
                text=result.text,
                citations=result.citations,
                grounding_status=GroundingStatus(result.grounding_status),
            )
            if not completed:
                await self._session.refresh(reply)
                await self._session.commit()
                yield "answer.completed", {
                    "reply": _message_response(reply).model_dump(mode="json")
                }
                return
            reply.text = result.text
            reply.citations = result.citations
            reply.grounding_status = GroundingStatus(result.grounding_status)
            reply.generation_status = GenerationStatus.COMPLETE
            await TelemetryService(self._session).record(
                message_id=reply.id,
                subject_id=subject_id,
                result=result,
                state="complete",
            )
            await self._session.commit()
            yield "answer.citations", {
                "replyId": reply.id,
                "citations": result.citations,
                "groundingStatus": result.grounding_status,
            }
            yield "answer.completed", {
                "reply": _message_response(reply).model_dump(mode="json")
            }
        except GenerationCancelled:
            await self._cancel_reply(reply.id, subject_id)
            await self._session.refresh(reply)
            await self._session.commit()
            yield "answer.completed", {
                "reply": _message_response(reply).model_dump(mode="json")
            }
        except (asyncio.CancelledError, GeneratorExit):
            await self._cancel_reply(reply.id, subject_id)
            await self._session.commit()
            raise
        except Exception:  # noqa: BLE001
            logger.exception("Answer stream failed reply=%s", reply.id)
            failed = await self._messages.fail_if_generating(reply.id)
            if not failed:
                await self._session.refresh(reply)
                await self._session.commit()
                yield "answer.completed", {
                    "reply": _message_response(reply).model_dump(mode="json")
                }
                return
            reply.generation_status = GenerationStatus.FAILED
            await TelemetryService(self._session).record(
                message_id=reply.id,
                subject_id=subject_id,
                state="failed",
                error_code="GENERATION_FAILED",
            )
            await self._session.commit()
            yield "answer.failed", {
                "replyId": reply.id,
                "code": "GENERATION_FAILED",
                "message": "Generation failed.",
            }

    async def _cancel_reply(self, reply_id, subject_id):
        if await self._messages.cancel_if_generating(reply_id):
            await TelemetryService(self._session).record(message_id=reply_id,
                subject_id=subject_id, state="cancelled")


def _message_response(msg: Message) -> MessageResponse:
    return MessageResponse(
        id=msg.id,
        role=msg.role.value,
        text=msg.text,
        createdAt=msg.created_at,
        citations=msg.citations or [],
        generationStatus=msg.generation_status.value,
        groundingStatus=msg.grounding_status.value if msg.grounding_status else None,
    )
