from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from db.models import ConversationKind, EvaluationCase, EvaluationRun, InstructorSubjectRole, MaterialStatus, User, UserRole
from helpers.config import get_settings
from helpers.errors import APIError, ErrorCode
from helpers.pagination import Page, PaginationParams
from repositories.evaluation_repository import EvaluationRepository
from repositories.feedback_repository import FeedbackRepository
from repositories.message_repository import MessageRepository
from repositories.conversation_repository import ConversationRepository
from repositories.material_repository import MaterialRepository
from repositories.subject_repository import SubjectRepository
from schemas.evaluation import (
    EvaluationCaseRequest,
    EvaluationCaseResponse,
    EvaluationResultResponse,
    EvaluationRunResponse,
    ReadinessResponse,
    FeedbackEvaluationCaseRequest,
)
from schemas.admin import FeedbackRowResponse


class EvaluationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = EvaluationRepository(session)
        self._subjects = SubjectRepository(session)
        self._materials = MaterialRepository(session)
        self._feedback = FeedbackRepository(session)
        self._messages = MessageRepository(session)
        self._conversations = ConversationRepository(session)

    async def _authorize(self, caller: User, subject_id: str, *, write: bool = False) -> None:
        if await self._subjects.get(subject_id) is None:
            raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Subject not found.")
        if caller.role == UserRole.ADMIN:
            return
        role = await self._subjects.get_instructor_role(subject_id, caller.id)
        required = InstructorSubjectRole.SUPER if write else None
        if role is None or (required and role != required):
            raise APIError(ErrorCode.FORBIDDEN, status.HTTP_403_FORBIDDEN, "Only the subject's super instructor can change evaluations.")

    async def list_cases(self, caller: User, subject_id: str):
        await self._authorize(caller, subject_id)
        return [_case_response(item) for item in await self._repo.list_cases(subject_id)]

    async def create_case(self, caller: User, subject_id: str, body: EvaluationCaseRequest):
        await self._authorize(caller, subject_id, write=True)
        case = await self._repo.add_case(EvaluationCase(
            subject_id=subject_id,
            question=body.question,
            reference_answer=body.referenceAnswer,
            expected_material_ids=body.expectedMaterialIds,
            tags=body.tags,
            active=body.active,
            created_by_id=caller.id,
        ))
        return _case_response(case)

    async def update_case(self, caller: User, subject_id: str, case_id: str, body: EvaluationCaseRequest):
        await self._authorize(caller, subject_id, write=True)
        case = await self._repo.get_case(case_id)
        if case is None or case.subject_id != subject_id:
            raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Evaluation case not found.")
        case.question = body.question
        case.reference_answer = body.referenceAnswer
        case.expected_material_ids = body.expectedMaterialIds
        case.tags = body.tags
        case.active = body.active
        case.updated_at = datetime.now(timezone.utc)
        return _case_response(case)

    async def delete_case(self, caller: User, subject_id: str, case_id: str) -> None:
        await self._authorize(caller, subject_id, write=True)
        case = await self._repo.get_case(case_id)
        if case is None or case.subject_id != subject_id:
            return
        await self._session.delete(case)

    async def create_run(self, caller: User, subject_id: str) -> EvaluationRunResponse:
        await self._authorize(caller, subject_id, write=True)
        if await self._repo.running_for_subject(subject_id):
            raise APIError(ErrorCode.CONFLICT, status.HTTP_409_CONFLICT, "An evaluation is already queued or running.")
        if await self._repo.active_case_count(subject_id) == 0:
            raise APIError(ErrorCode.CONFLICT, status.HTTP_409_CONFLICT, "Add at least one active evaluation case first.")
        try:
            run = await self._repo.add_run(EvaluationRun(
                subject_id=subject_id,
                corpus_version=await self.corpus_version(subject_id),
                pipeline_snapshot=_pipeline_snapshot(),
                created_by_id=caller.id,
            ))
        except IntegrityError as exc:
            await self._session.rollback()
            raise APIError(
                ErrorCode.CONFLICT,
                status.HTTP_409_CONFLICT,
                "An evaluation is already queued or running.",
            ) from exc
        return _run_response(run)

    async def review_feedback(
        self, caller: User, subject_id: str, params: PaginationParams
    ) -> Page[FeedbackRowResponse]:
        await self._authorize(caller, subject_id)
        rows, total = await self._feedback.list_rows(
            semester=None,
            subject_id=subject_id,
            feedback=None,
            search=params.search,
            offset=params.offset,
            limit=params.page_size,
        )
        return Page.build(
            items=[FeedbackRowResponse(**row) for row in rows],
            total=total,
            params=params,
        )

    async def case_from_feedback(
        self,
        caller: User,
        subject_id: str,
        feedback_id: str,
        body: FeedbackEvaluationCaseRequest,
    ):
        await self._authorize(caller, subject_id, write=True)
        feedback = await self._feedback.get(feedback_id)
        if feedback is None:
            raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Feedback not found.")
        message = await self._messages.get(feedback.message_id)
        conversation = await self._conversations.get(message.conversation_id) if message else None
        if (
            message is None
            or conversation is None
            or conversation.kind != ConversationKind.TUTOR
            or conversation.subject_id != subject_id
        ):
            raise APIError(ErrorCode.FORBIDDEN, status.HTTP_403_FORBIDDEN, "Private document feedback cannot be opened or converted.")
        question = await self._messages.previous_user_message(conversation.id, message.sort_id)
        if question is None:
            raise APIError(ErrorCode.CONFLICT, status.HTTP_409_CONFLICT, "The feedback has no preceding student question.")
        case = await self._repo.add_case(EvaluationCase(
            subject_id=subject_id,
            question=question.text,
            reference_answer=body.referenceAnswer,
            expected_material_ids=body.expectedMaterialIds or [c.get("sourceId") for c in (message.citations or []) if c.get("sourceId")],
            tags=list(dict.fromkeys(["feedback", feedback.reason.value if feedback.reason else "review", *body.tags])),
            active=True,
            created_by_id=caller.id,
        ))
        feedback.evaluation_case_id = case.id
        return _case_response(case)

    async def list_runs(self, caller: User, subject_id: str | None = None):
        if subject_id:
            await self._authorize(caller, subject_id)
        elif caller.role != UserRole.ADMIN:
            raise APIError(ErrorCode.FORBIDDEN, status.HTTP_403_FORBIDDEN, "Admin access required.")
        return [_run_response(run) for run in await self._repo.list_runs(subject_id)]

    async def get_run(self, caller: User, run_id: str):
        run = await self._repo.get_run(run_id)
        if run is None:
            raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Evaluation run not found.")
        await self._authorize(caller, run.subject_id)
        return _run_response(run)

    async def results(self, caller: User, run_id: str):
        run = await self._repo.get_run(run_id)
        if run is None:
            raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Evaluation run not found.")
        await self._authorize(caller, run.subject_id)
        return [_result_response(item) for item in await self._repo.list_results(run_id)]

    async def readiness(self, caller: User, subject_id: str) -> ReadinessResponse:
        await self._authorize(caller, subject_id)
        materials = list(await self._materials.list_for_subject(subject_id))
        processed = sum(item.status == MaterialStatus.PROCESSED for item in materials)
        failed = sum(item.status == MaterialStatus.FAILED for item in materials)
        active_cases = await self._repo.active_case_count(subject_id)
        latest = await self._repo.latest_completed(subject_id)
        reasons: list[str] = []
        metrics = latest.summary_metrics if latest else {}
        if processed == 0:
            reasons.append("no_processed_materials")
        if active_cases < 20:
            reasons.append("fewer_than_20_active_cases")
        state = "needs_setup" if reasons else "healthy"
        if state != "needs_setup":
            if failed:
                reasons.append("failed_materials")
            current_corpus = _corpus_version(materials)
            if latest is None or latest.corpus_version != current_corpus:
                reasons.append("stale_evaluation")
            if metrics.get("correctness", 0) < 0.80:
                reasons.append("correctness_below_0_80")
            if metrics.get("faithfulness", 0) < 0.90:
                reasons.append("faithfulness_below_0_90")
            if metrics.get("citationCoverage", 0) < 0.95:
                reasons.append("citation_coverage_below_0_95")
            if reasons:
                state = "needs_review"
        return ReadinessResponse(
            subjectId=subject_id,
            state=state,
            reasons=reasons,
            activeCases=active_cases,
            processedMaterials=processed,
            failedMaterials=failed,
            latestRunId=latest.id if latest else None,
            metrics=metrics,
        )

    async def corpus_version(self, subject_id: str) -> str:
        materials = await self._materials.list_for_subject(subject_id)
        return _corpus_version(materials)


def _corpus_version(materials) -> str:
    value = [(m.id, m.status.value, m.updated_at.isoformat()) for m in materials]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:24]


def _pipeline_snapshot() -> dict:
    settings = get_settings()
    return {
        "generationBackend": settings.GENERATION_BACKEND,
        "generationModel": settings.GENERATION_MODEL_ID,
        "embeddingBackend": settings.EMBEDDING_BACKEND,
        "rerankEnabled": settings.RERANK_ENABLED,
        "rerankBackend": settings.RERANK_BACKEND,
        "rerankTopN": settings.RERANK_TOP_N,
        "mmrEnabled": settings.MMR_ENABLED,
        "mmrLambda": settings.MMR_LAMBDA,
        "retrievalLimit": settings.AGENT_RETRIEVAL_LIMIT,
        "retrievalThreshold": settings.AGENT_RETRIEVAL_THRESHOLD,
    }


def _case_response(case: EvaluationCase) -> EvaluationCaseResponse:
    return EvaluationCaseResponse(id=case.id, subjectId=case.subject_id, question=case.question, referenceAnswer=case.reference_answer, expectedMaterialIds=case.expected_material_ids or [], tags=case.tags or [], active=case.active, createdBy=case.created_by_id, createdAt=case.created_at, updatedAt=case.updated_at)


def _run_response(run) -> EvaluationRunResponse:
    return EvaluationRunResponse(id=run.id, subjectId=run.subject_id, status=run.status.value, corpusVersion=run.corpus_version, pipelineSnapshot=run.pipeline_snapshot or {}, summaryMetrics=run.summary_metrics or {}, failure=run.failure, createdAt=run.created_at, startedAt=run.started_at, completedAt=run.completed_at)


def _result_response(result) -> EvaluationResultResponse:
    return EvaluationResultResponse(id=result.id, runId=result.run_id, caseId=result.case_id, generatedAnswer=result.generated_answer, citations=result.citations or [], metrics=result.metrics or {}, failureInfo=result.failure_info)
