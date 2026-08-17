from datetime import datetime, timedelta, timezone

from db.models import EvaluationCase, EvaluationRun, EvaluationRunStatus
from repositories.evaluation_repository import EvaluationRepository
from services.answer_result import AnswerResult
from services.evaluation_service import EvaluationService
from workers.evaluation_worker import process_next


async def test_worker_retries_provider_and_records_partial_failure(seed, db):
    instructor = await seed.instructor(username="worker_super")
    await seed.subject(id="worker-sub", instructors=[instructor], super_id=instructor)
    repo = EvaluationRepository(db)
    first = await repo.add_case(EvaluationCase(
        subject_id="worker-sub", question="retry me", reference_answer="correct answer",
        created_by_id=instructor.id,
    ))
    second = await repo.add_case(EvaluationCase(
        subject_id="worker-sub", question="always fail", reference_answer="reference",
        created_by_id=instructor.id,
    ))
    run = await repo.add_run(EvaluationRun(
        subject_id="worker-sub",
        corpus_version=await EvaluationService(db).corpus_version("worker-sub"),
        pipeline_snapshot={"retrievalLimit": 5, "retrievalThreshold": 0.3},
        created_by_id=instructor.id,
    ))
    await db.commit()
    attempts = {first.question: 0, second.question: 0}

    class FlakyRag:
        async def answer(self, _collection, question, **_kwargs):
            attempts[question] += 1
            if question == first.question and attempts[question] < 3:
                raise RuntimeError("temporary provider error")
            if question == second.question:
                raise RuntimeError("permanent provider error")
            return AnswerResult(
                text="correct answer",
                citations=[{"id": "cite"}],
                grounding_status="grounded",
                latency_ms=25,
            )

    assert await process_next(db, FlakyRag()) is True
    await db.refresh(run)
    results = await repo.list_results(run.id)
    assert run.status == EvaluationRunStatus.COMPLETED
    assert attempts[first.question] == 3
    assert attempts[second.question] == 3
    assert len(results) == 2
    failed = next(item for item in results if item.case_id == second.id)
    assert failed.failure_info["attempts"] == 3
    assert run.summary_metrics["errorRate"] == 0.5


async def test_stale_running_job_is_requeued(seed, db):
    instructor = await seed.instructor(username="recovery_super")
    await seed.subject(id="recovery-sub", instructors=[instructor], super_id=instructor)
    repo = EvaluationRepository(db)
    run = await repo.add_run(EvaluationRun(
        subject_id="recovery-sub",
        status=EvaluationRunStatus.RUNNING,
        started_at=datetime.now(timezone.utc) - timedelta(hours=1),
        corpus_version="v1",
        pipeline_snapshot={},
        created_by_id=instructor.id,
    ))
    await db.commit()
    recovered = await repo.recover_stale_runs(
        datetime.now(timezone.utc) - timedelta(minutes=15)
    )
    await db.commit()
    await db.refresh(run)
    assert recovered == 1
    assert run.status == EvaluationRunStatus.QUEUED
    assert run.started_at is None
