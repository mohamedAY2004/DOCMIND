"""Authorized stateless previews sharing student retrieval configuration."""
import logging
import uuid

from db.models import SemesterState, UserRole
from helpers.config import get_settings
from helpers.errors import APIError, ErrorCode
from repositories.material_repository import MaterialRepository
from repositories.subject_repository import SubjectRepository
from schemas.material import TestBotResponse
from services.generation_control import GenerationSlot
from services.generation_source import generate_answer
from services.rag_service import collection_for_subject
from services.subject_corpus_service import build_subject_corpus

logger = logging.getLogger("docmind.preview")


class PreviewService:
    def __init__(self, session, rag, agent, store):
        self._session, self._rag, self._agent, self._store = session, rag, agent, store

    async def _prepare(self, user, subject_id, text):
        subjects = SubjectRepository(self._session)
        subject = await subjects.get(subject_id)
        if subject is None:
            raise APIError(ErrorCode.NOT_FOUND, 404, "Subject not found.")
        if user.role != UserRole.ADMIN and not await subjects.is_instructor_of(subject_id, user.id):
            raise APIError(ErrorCode.FORBIDDEN, 403, "You are not assigned to this subject.")
        if await subjects.semester_state_for_subject(subject_id) is SemesterState.ARCHIVED:
            raise APIError(ErrorCode.FORBIDDEN, 403, "This semester is archived; the assistant is offline and cannot be tested.")
        if await MaterialRepository(self._session).count_processed(subject_id) == 0:
            raise APIError(ErrorCode.SUBJECT_NOT_READY, 409, "This subject has no indexed materials yet.")
        manifest, materials = await build_subject_corpus(self._session, subject_id)
        return dict(collection=collection_for_subject(subject_id), text=text, source_kind="material",
                    subject_name=f"{subject.course_code} — {subject.title}",
                    subject_manifest=manifest, material_index=materials)

    async def reply(self, user, subject_id, text):
        context = await self._prepare(user, subject_id, text)
        slot = await GenerationSlot.acquire(self._store, user.id)
        try:
            result = None
            async for kind, value in generate_answer(self._rag, self._agent, streaming=False, **context):
                if kind == "result":
                    result = value
            if result is None:
                raise RuntimeError("Generation completed without a result")
            return TestBotResponse(reply=result.text)
        finally:
            await slot.release()

    async def stream(self, user, subject_id, text):
        if not get_settings().STREAMING_CHAT:
            raise APIError(ErrorCode.NOT_FOUND, 404, "Streaming chat is disabled.")
        context = await self._prepare(user, subject_id, text)
        slot = await GenerationSlot.acquire(self._store, user.id)
        return self._events(slot, context)

    async def _events(self, slot, context):
        reply_id = "preview_" + uuid.uuid4().hex[:20]
        reply = dict(id=reply_id, role="assistant", text="", citations=[],
                     generationStatus="generating", groundingStatus=None)
        try:
            yield "message.created", {"reply": reply}
            result = None
            async for kind, value in generate_answer(self._rag, self._agent, **context):
                if kind == "delta":
                    yield "answer.delta", {"replyId": reply_id, "delta": value}
                else:
                    result = value
            if result is None:
                raise RuntimeError("Generation completed without a result")
            yield "answer.citations", dict(replyId=reply_id, citations=result.citations,
                                            groundingStatus=result.grounding_status)
            yield "answer.completed", {"reply": dict(reply, text=result.text,
                citations=result.citations, groundingStatus=result.grounding_status,
                generationStatus="complete")}
        except Exception:
            logger.exception("Instructor preview generation failed")
            yield "answer.failed", dict(replyId=reply_id, code="GENERATION_FAILED", message="Generation failed.")
        finally:
            await slot.release()
