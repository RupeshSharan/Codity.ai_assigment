from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DeadLetterEntry
from app.models.enums import JobStatus
from app.schemas.job import JobCreate
from app.services.jobs import claim_next_job, create_job, fail_job, start_job


def test_failed_job_retries_then_moves_to_dead_letter(db_session: Session, seeded) -> None:
    job = create_job(db_session, JobCreate(queue_id=seeded.queue.id, payload={"action": "fail"}))

    first_claim = claim_next_job(db_session, worker_id=seeded.worker.id)
    assert first_claim is not None
    start_job(db_session, first_claim.id, seeded.worker.id)
    first_failure = fail_job(db_session, first_claim.id, seeded.worker.id, "temporary outage")

    assert first_failure.status == JobStatus.SCHEDULED
    assert first_failure.retry_count == 1
    assert first_failure.locked_by_worker_id is None

    second_claim = claim_next_job(
        db_session,
        worker_id=seeded.worker.id,
        now=first_failure.scheduled_at + timedelta(seconds=1),
    )
    assert second_claim is not None
    start_job(db_session, second_claim.id, seeded.worker.id)
    exhausted = fail_job(db_session, second_claim.id, seeded.worker.id, "still broken")

    assert exhausted.status == JobStatus.DEAD_LETTER
    assert exhausted.retry_count == seeded.retry_policy.max_attempts

    entry = db_session.execute(
        select(DeadLetterEntry).where(DeadLetterEntry.job_id == job.id)
    ).scalar_one()
    assert entry.reason == "max_attempts_exhausted"
    assert entry.failed_attempts == seeded.retry_policy.max_attempts
    assert entry.last_error == "still broken"

