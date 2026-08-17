from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select, update

from db.models import EvaluationCase, EvaluationResult, EvaluationRun, EvaluationRunStatus
from .base import BaseRepository


class EvaluationRepository(BaseRepository):
    async def add_case(self, case: EvaluationCase) -> EvaluationCase:
        self.session.add(case)
        await self.session.flush()
        return case

    async def get_case(self, case_id: str) -> EvaluationCase | None:
        return await self.session.get(EvaluationCase, case_id)

    async def list_cases(self, subject_id: str, *, active_only: bool = False):
        stmt = select(EvaluationCase).where(EvaluationCase.subject_id == subject_id)
        if active_only:
            stmt = stmt.where(EvaluationCase.active.is_(True))
        return (await self.session.execute(stmt.order_by(EvaluationCase.created_at))).scalars().all()

    async def active_case_count(self, subject_id: str) -> int:
        value = await self.session.scalar(select(func.count(EvaluationCase.id)).where(EvaluationCase.subject_id == subject_id, EvaluationCase.active.is_(True)))
        return int(value or 0)

    async def add_run(self, run: EvaluationRun) -> EvaluationRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def get_run(self, run_id: str) -> EvaluationRun | None:
        return await self.session.get(EvaluationRun, run_id)

    async def running_for_subject(self, subject_id: str) -> EvaluationRun | None:
        stmt = select(EvaluationRun).where(
            EvaluationRun.subject_id == subject_id,
            EvaluationRun.status.in_([EvaluationRunStatus.QUEUED, EvaluationRunStatus.RUNNING]),
        ).limit(1)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_runs(self, subject_id: str | None = None):
        stmt = select(EvaluationRun)
        if subject_id:
            stmt = stmt.where(EvaluationRun.subject_id == subject_id)
        return (await self.session.execute(stmt.order_by(EvaluationRun.created_at.desc()))).scalars().all()

    async def latest_completed(self, subject_id: str) -> EvaluationRun | None:
        stmt = select(EvaluationRun).where(
            EvaluationRun.subject_id == subject_id,
            EvaluationRun.status == EvaluationRunStatus.COMPLETED,
        ).order_by(EvaluationRun.completed_at.desc()).limit(1)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def add_result(self, result: EvaluationResult) -> EvaluationResult:
        self.session.add(result)
        await self.session.flush()
        return result

    async def list_results(self, run_id: str):
        return (await self.session.execute(select(EvaluationResult).where(EvaluationResult.run_id == run_id).order_by(EvaluationResult.created_at))).scalars().all()

    async def next_queued(self) -> EvaluationRun | None:
        stmt = select(EvaluationRun).where(EvaluationRun.status == EvaluationRunStatus.QUEUED).order_by(EvaluationRun.created_at).with_for_update(skip_locked=True).limit(1)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def queued_count(self) -> int:
        value = await self.session.scalar(
            select(func.count(EvaluationRun.id)).where(
                EvaluationRun.status == EvaluationRunStatus.QUEUED
            )
        )
        return int(value or 0)

    async def recover_stale_runs(self, cutoff: datetime) -> int:
        result = await self.session.execute(
            update(EvaluationRun)
            .where(
                EvaluationRun.status == EvaluationRunStatus.RUNNING,
                EvaluationRun.started_at < cutoff,
            )
            .values(status=EvaluationRunStatus.QUEUED, started_at=None)
        )
        return int(result.rowcount or 0)
