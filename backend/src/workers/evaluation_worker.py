"""Database-durable evaluation worker; Redis is used by deployments for wakeups."""
from __future__ import annotations

import argparse
import asyncio
import re
from datetime import datetime, timedelta, timezone

from db.models import EvaluationResult, EvaluationRunStatus
from repositories.evaluation_repository import EvaluationRepository
from repositories.subject_repository import SubjectRepository
from services.evaluation_service import EvaluationService
from services.rag_service import collection_for_subject
from helpers.config import get_settings


async def process_next(session, rag) -> bool:
    repo = EvaluationRepository(session)
    from services.telemetry_service import metrics
    run = await repo.next_queued()
    if run is None:
        return False
    run.status = EvaluationRunStatus.RUNNING
    metrics.set_gauge("evaluation_worker_backlog", await repo.queued_count())
    run.started_at = datetime.now(timezone.utc)
    await session.commit()

    try:
        cases = await repo.list_cases(run.subject_id, active_only=True)
        subject = await SubjectRepository(session).get(run.subject_id)
        subject_name = f"{subject.course_code} — {subject.title}" if subject else "Unknown"
        previous = list(await repo.list_results(run.id))
        completed_case_ids = {item.case_id for item in previous}
        metrics_rows: list[dict] = [item.metrics or {"error": 1.0} for item in previous]
        for case in cases:
            if case.id in completed_case_ids:
                continue
            last_error = None
            retries = max(1, get_settings().EVALUATION_CASE_RETRIES)
            for attempt in range(1, retries + 1):
                try:
                    answer = await rag.answer(
                        collection_for_subject(run.subject_id),
                        case.question,
                        limit=int(run.pipeline_snapshot.get("retrievalLimit", 5)),
                        threshold=float(run.pipeline_snapshot.get("retrievalThreshold", 0.3)),
                        subject_name=subject_name,
                    )
                    metrics = _score(case.reference_answer, answer.text, answer.grounding_status, answer.citations, answer.latency_ms)
                    metrics_rows.append(metrics)
                    await repo.add_result(EvaluationResult(
                        run_id=run.id,
                        case_id=case.id,
                        generated_answer=answer.text,
                        citations=answer.citations,
                        metrics=metrics,
                    ))
                    last_error = None
                    break
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    if attempt < retries:
                        await asyncio.sleep(min(1.0, 0.1 * (2 ** (attempt - 1))))
            if last_error is not None:
                metrics_rows.append({"error": 1.0})
                await repo.add_result(EvaluationResult(
                    run_id=run.id,
                    case_id=case.id,
                    failure_info={"code": "GENERATION_FAILED", "message": str(last_error), "attempts": retries},
                ))
            await session.commit()

        current_corpus = await EvaluationService(session).corpus_version(run.subject_id)
        if current_corpus != run.corpus_version:
            raise RuntimeError("Corpus changed while the evaluation was running.")
        run.summary_metrics = _summarize(metrics_rows)
        run.status = EvaluationRunStatus.COMPLETED
        run.completed_at = datetime.now(timezone.utc)
        await session.commit()
    except Exception as exc:  # noqa: BLE001
        run.status = EvaluationRunStatus.FAILED
        run.failure = str(exc)
        run.completed_at = datetime.now(timezone.utc)
        await session.commit()
    return True


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[\w']+", (value or "").lower()))


def _score(reference: str, answer: str, grounding: str, citations: list, latency_ms: int) -> dict:
    expected, actual = _tokens(reference), _tokens(answer)
    overlap = len(expected & actual)
    precision = overlap / len(actual) if actual else 0.0
    recall = overlap / len(expected) if expected else 0.0
    correctness = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    faithfulness = {"grounded": 1.0, "partially_grounded": 0.5, "ungrounded": 0.0, "no_context": 0.0}.get(grounding, 0.0)
    citation_coverage = 1.0 if citations and grounding == "grounded" else 0.5 if citations else 0.0
    return {"correctness": correctness, "faithfulness": faithfulness, "citationCoverage": citation_coverage, "latencyMs": latency_ms, "error": 0.0}


def _summarize(rows: list[dict]) -> dict:
    if not rows:
        return {"correctness": 0.0, "faithfulness": 0.0, "citationCoverage": 0.0, "meanLatencyMs": 0, "errorRate": 1.0, "cases": 0}
    def mean(key):
        return sum(float(row.get(key, 0)) for row in rows) / len(rows)
    return {"correctness": mean("correctness"), "faithfulness": mean("faithfulness"), "citationCoverage": mean("citationCoverage"), "meanLatencyMs": round(mean("latencyMs")), "errorRate": mean("error"), "cases": len(rows)}


async def _main(once: bool) -> None:
    from main import _shutdown, _startup, app
    from routes.chat_tutor_router import _rag
    from services.ephemeral_store import store_for
    from starlette.requests import Request

    await _startup()
    try:
        scope = {"type": "http", "app": app, "headers": [], "method": "GET", "path": "/", "query_string": b"", "server": ("worker", 0), "client": ("worker", 0), "scheme": "http"}
        rag = _rag(Request(scope))
        store = store_for(app)
        async with app.state.session_maker() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(
                minutes=get_settings().EVALUATION_RUN_STALE_MINUTES
            )
            await EvaluationRepository(session).recover_stale_runs(cutoff)
            await session.commit()
        while True:
            async with app.state.session_maker() as session:
                worked = await process_next(session, rag)
            if once:
                return
            if not worked:
                await store.dequeue("evaluation:runs", timeout_seconds=5)
    finally:
        await _shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    asyncio.run(_main(parser.parse_args().once))
