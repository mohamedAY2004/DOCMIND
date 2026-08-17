from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, UserRole
from helpers.deps import get_session, require_role
from helpers.config import get_settings
from helpers.errors import APIError, ErrorCode
from helpers.pagination import Page, PaginationParams, pagination_query
from schemas.admin import FeedbackRowResponse
from schemas.evaluation import EvaluationCaseRequest, EvaluationCaseResponse, EvaluationResultResponse, EvaluationRunResponse, FeedbackEvaluationCaseRequest, ReadinessResponse
from services.evaluation_service import EvaluationService
from services.ephemeral_store import store_for

router = APIRouter(prefix="/subjects/{subject_id}", tags=["evaluation"])
admin_router = APIRouter(prefix="/admin/evaluations", tags=["admin", "evaluation"])


@router.get("/evaluation-cases", response_model=list[EvaluationCaseResponse])
async def list_cases(subject_id: str, session: AsyncSession = Depends(get_session), caller: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN))):
    return await EvaluationService(session).list_cases(caller, subject_id)


@router.post("/evaluation-cases", response_model=EvaluationCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(subject_id: str, body: EvaluationCaseRequest, session: AsyncSession = Depends(get_session), caller: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN))):
    return await EvaluationService(session).create_case(caller, subject_id, body)


@router.put("/evaluation-cases/{case_id}", response_model=EvaluationCaseResponse)
async def update_case(subject_id: str, case_id: str, body: EvaluationCaseRequest, session: AsyncSession = Depends(get_session), caller: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN))):
    return await EvaluationService(session).update_case(caller, subject_id, case_id, body)


@router.delete("/evaluation-cases/{case_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_case(subject_id: str, case_id: str, session: AsyncSession = Depends(get_session), caller: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN))):
    await EvaluationService(session).delete_case(caller, subject_id, case_id)


@router.post("/evaluation-runs", response_model=EvaluationRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_run(subject_id: str, request: Request, session: AsyncSession = Depends(get_session), caller: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN))):
    run = await EvaluationService(session).create_run(caller, subject_id)
    # The database row is the durable source of truth; Redis only wakes a
    # worker promptly. A worker restart still discovers queued rows.
    await store_for(request.app).enqueue("evaluation:runs", run.id)
    return run


@router.post("/feedback/{feedback_id}/evaluation-case", response_model=EvaluationCaseResponse, status_code=status.HTTP_201_CREATED)
async def feedback_to_case(subject_id: str, feedback_id: str, body: FeedbackEvaluationCaseRequest, session: AsyncSession = Depends(get_session), caller: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN))):
    return await EvaluationService(session).case_from_feedback(caller, subject_id, feedback_id, body)


@router.get("/feedback", response_model=Page[FeedbackRowResponse])
async def review_feedback(subject_id: str, session: AsyncSession = Depends(get_session), caller: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN)), params: PaginationParams = Depends(pagination_query)):
    return await EvaluationService(session).review_feedback(caller, subject_id, params)


@router.get("/evaluation-runs", response_model=list[EvaluationRunResponse])
async def list_runs(subject_id: str, session: AsyncSession = Depends(get_session), caller: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN))):
    return await EvaluationService(session).list_runs(caller, subject_id)


@router.get("/evaluation-runs/{run_id}", response_model=EvaluationRunResponse)
async def get_run(subject_id: str, run_id: str, session: AsyncSession = Depends(get_session), caller: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN))):
    return await EvaluationService(session).get_run(caller, run_id)


@router.get("/evaluation-runs/{run_id}/results", response_model=list[EvaluationResultResponse])
async def get_results(subject_id: str, run_id: str, session: AsyncSession = Depends(get_session), caller: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN))):
    return await EvaluationService(session).results(caller, run_id)


@router.get("/readiness", response_model=ReadinessResponse)
async def readiness(subject_id: str, session: AsyncSession = Depends(get_session), caller: User = Depends(require_role(UserRole.INSTRUCTOR, UserRole.ADMIN))):
    if not get_settings().SUBJECT_READINESS:
        raise APIError(ErrorCode.NOT_FOUND, status.HTTP_404_NOT_FOUND, "Subject readiness is disabled.")
    return await EvaluationService(session).readiness(caller, subject_id)


@admin_router.get("/runs", response_model=list[EvaluationRunResponse])
async def all_runs(session: AsyncSession = Depends(get_session), admin: User = Depends(require_role(UserRole.ADMIN))):
    return await EvaluationService(session).list_runs(admin)
