from datetime import datetime, timedelta
import uuid

from sqlalchemy import Select, and_, func, or_, select, update
from sqlalchemy.orm import Session

from app.core.exceptions import DomainError, NotFoundError
from app.models import (
    DeadLetterEntry,
    ExecutionStatus,
    Job,
    JobExecution,
    JobKind,
    JobLog,
    JobStatus,
    Queue,
    QueueStatus,
    RetryPolicy,
    Worker,
    WorkerStatus,
)
from app.schemas.job import BatchJobCreate, JobCreate
from app.services.retry import next_retry_time


ACTIVE_JOB_STATUSES = (JobStatus.CLAIMED, JobStatus.RUNNING)


def _job_claim_scan(queue_ids: list[str] | None = None, now: datetime | None = None) -> Select:
    current = now or datetime.utcnow()
    active_count = (
        select(func.count(Job.id))
        .where(Job.queue_id == Queue.id, Job.status.in_(ACTIVE_JOB_STATUSES))
        .correlate(Queue)
        .scalar_subquery()
    )
    stmt = (
        select(Job)
        .join(Queue, Queue.id == Job.queue_id)
        .where(
            Queue.status == QueueStatus.ACTIVE,
            Job.status == JobStatus.QUEUED,
            Job.scheduled_at <= current,
            active_count < Queue.max_concurrency,
        )
        .order_by(Job.priority.desc(), Queue.priority.desc(), Job.scheduled_at.asc(), Job.created_at.asc())
        .limit(1)
    )
    if queue_ids:
        stmt = stmt.where(Job.queue_id.in_(queue_ids))
    return stmt


def promote_due_scheduled_jobs(db: Session, now: datetime | None = None) -> int:
    current = now or datetime.utcnow()
    result = db.execute(
        update(Job)
        .where(Job.status == JobStatus.SCHEDULED, Job.scheduled_at <= current)
        .values(status=JobStatus.QUEUED, updated_at=current)
    )
    db.commit()
    return result.rowcount or 0


def create_job(db: Session, job_in: JobCreate) -> Job:
    queue = db.get(Queue, job_in.queue_id)
    if queue is None:
        raise NotFoundError("Queue not found.")
    now = datetime.utcnow()
    scheduled_at = job_in.scheduled_at or now
    if job_in.delay_seconds is not None:
        scheduled_at = now + timedelta(seconds=job_in.delay_seconds)
    status = JobStatus.SCHEDULED if scheduled_at > now else JobStatus.QUEUED
    retry_policy_id = job_in.retry_policy_id or queue.retry_policy_id
    if job_in.idempotency_key:
        existing = db.execute(
            select(Job).where(
                Job.project_id == queue.project_id,
                Job.idempotency_key == job_in.idempotency_key,
            )
        ).scalar_one_or_none()
        if existing:
            return existing
    job = Job(
        project_id=queue.project_id,
        queue_id=queue.id,
        retry_policy_id=retry_policy_id,
        batch_id=job_in.batch_id,
        kind=job_in.kind,
        status=status,
        payload=job_in.payload,
        job_metadata=job_in.metadata,
        tags=job_in.tags,
        priority=job_in.priority,
        scheduled_at=scheduled_at,
        timeout_seconds=job_in.timeout_seconds,
        cron_expression=job_in.cron_expression,
        idempotency_key=job_in.idempotency_key,
        max_attempts=job_in.max_attempts,
    )
    db.add(job)
    db.flush()
    append_job_log(db, job, "INFO", "Job created.", {"status": status.value})
    db.commit()
    db.refresh(job)
    return job


def create_batch(db: Session, batch_in: BatchJobCreate) -> list[Job]:
    batch_id = batch_in.batch_id or str(uuid.uuid4())
    jobs: list[Job] = []
    for item in batch_in.jobs:
        job_in = JobCreate(**item.model_dump(), queue_id=batch_in.queue_id, batch_id=batch_id, kind=JobKind.BATCH)
        jobs.append(create_job(db, job_in))
    return jobs


def claim_next_job(
    db: Session,
    *,
    worker_id: str,
    queue_ids: list[str] | None = None,
    now: datetime | None = None,
) -> Job | None:
    current = now or datetime.utcnow()
    worker = db.get(Worker, worker_id)
    if worker is None:
        raise NotFoundError("Worker not registered.")
    if worker.status != WorkerStatus.ONLINE:
        raise DomainError("Worker is not accepting jobs.")

    promote_due_scheduled_jobs(db, current)
    dialect = db.bind.dialect.name if db.bind else ""
    if dialect == "postgresql":
        stmt = _job_claim_scan(queue_ids, current).with_for_update(skip_locked=True)
        job = db.execute(stmt).scalar_one_or_none()
        if job is None:
            db.rollback()
            return None
        job.status = JobStatus.CLAIMED
        job.claimed_at = current
        job.locked_by_worker_id = worker_id
        append_job_log(db, job, "INFO", "Job claimed.", {"worker_id": worker_id})
        db.commit()
        db.refresh(job)
        return job

    candidate = _job_claim_scan(queue_ids, current).with_only_columns(Job.id)
    job_id = db.execute(candidate).scalar_one_or_none()
    if job_id is None:
        db.rollback()
        return None
    result = db.execute(
        update(Job)
        .where(Job.id == job_id, Job.status == JobStatus.QUEUED)
        .values(
            status=JobStatus.CLAIMED,
            claimed_at=current,
            locked_by_worker_id=worker_id,
            updated_at=current,
        )
    )
    if result.rowcount != 1:
        db.rollback()
        return None
    job = db.get(Job, job_id)
    append_job_log(db, job, "INFO", "Job claimed.", {"worker_id": worker_id})
    db.commit()
    db.refresh(job)
    return job


def start_job(db: Session, job_id: str, worker_id: str) -> JobExecution:
    job = db.get(Job, job_id)
    if job is None:
        raise NotFoundError("Job not found.")
    if job.status not in {JobStatus.CLAIMED, JobStatus.QUEUED}:
        raise DomainError(f"Cannot start job while status is {job.status}.")
    now = datetime.utcnow()
    job.status = JobStatus.RUNNING
    job.started_at = now
    job.locked_by_worker_id = worker_id
    execution = JobExecution(
        job_id=job.id,
        worker_id=worker_id,
        attempt_number=job.retry_count + 1,
        status=ExecutionStatus.RUNNING,
        started_at=now,
    )
    db.add(execution)
    append_job_log(db, job, "INFO", "Job started.", {"worker_id": worker_id})
    db.commit()
    db.refresh(execution)
    return execution


def complete_job(db: Session, job_id: str, worker_id: str, result: dict | None = None) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise NotFoundError("Job not found.")
    if job.locked_by_worker_id != worker_id:
        raise DomainError("Worker does not own this job claim.", status_code=409)
    now = datetime.utcnow()
    job.status = JobStatus.COMPLETED
    job.completed_at = now
    job.last_error = None
    execution = _latest_running_execution(db, job.id, worker_id)
    if execution:
        execution.status = ExecutionStatus.SUCCEEDED
        execution.completed_at = now
        execution.duration_ms = _duration_ms(execution.started_at, now)
        execution.result = result or {}
    append_job_log(db, job, "INFO", "Job completed.", {"worker_id": worker_id})
    db.commit()
    db.refresh(job)
    return job


def fail_job(db: Session, job_id: str, worker_id: str, error: str) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise NotFoundError("Job not found.")
    if job.locked_by_worker_id != worker_id:
        raise DomainError("Worker does not own this job claim.", status_code=409)
    now = datetime.utcnow()
    job.retry_count += 1
    job.last_error = error
    execution = _latest_running_execution(db, job.id, worker_id)
    if execution:
        execution.status = ExecutionStatus.FAILED
        execution.completed_at = now
        execution.duration_ms = _duration_ms(execution.started_at, now)
        execution.error = error

    policy = _job_retry_policy(db, job)
    max_attempts = job.max_attempts or (policy.max_attempts if policy else 1)
    if job.retry_count >= max_attempts:
        job.status = JobStatus.DEAD_LETTER
        job.failed_at = now
        job.locked_by_worker_id = None
        db.add(
            DeadLetterEntry(
                job_id=job.id,
                queue_id=job.queue_id,
                reason="max_attempts_exhausted",
                failed_attempts=job.retry_count,
                payload_snapshot=job.payload,
                last_error=error,
            )
        )
        append_job_log(db, job, "ERROR", "Job moved to Dead Letter Queue.", {"error": error})
    else:
        next_attempt = job.retry_count + 1
        job.status = JobStatus.SCHEDULED
        job.scheduled_at = next_retry_time(policy, next_attempt, now) if policy else now
        job.locked_by_worker_id = None
        append_job_log(
            db,
            job,
            "WARNING",
            "Job failed and was scheduled for retry.",
            {"error": error, "next_attempt": next_attempt, "scheduled_at": job.scheduled_at.isoformat()},
        )
    db.commit()
    db.refresh(job)
    return job


def retry_dead_letter_job(db: Session, job_id: str) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise NotFoundError("Job not found.")
    if job.status != JobStatus.DEAD_LETTER:
        raise DomainError("Only dead-letter jobs can be retried.")
    entry = db.execute(select(DeadLetterEntry).where(DeadLetterEntry.job_id == job_id)).scalar_one_or_none()
    if entry:
        entry.retried_at = datetime.utcnow()
    job.status = JobStatus.QUEUED
    job.retry_count = 0
    job.failed_at = None
    job.last_error = None
    job.scheduled_at = datetime.utcnow()
    append_job_log(db, job, "INFO", "Dead-letter job requeued by operator.", {})
    db.commit()
    db.refresh(job)
    return job


def recover_stale_jobs(db: Session, stale_before: datetime) -> int:
    stale_workers = select(Worker.id).where(Worker.last_heartbeat_at < stale_before)
    jobs = db.execute(
        select(Job).where(
            Job.status.in_(ACTIVE_JOB_STATUSES),
            Job.locked_by_worker_id.in_(stale_workers),
        )
    ).scalars()
    recovered = 0
    for job in jobs:
        job.status = JobStatus.SCHEDULED
        job.scheduled_at = datetime.utcnow()
        job.locked_by_worker_id = None
        append_job_log(db, job, "WARNING", "Job recovered from stale worker.", {})
        recovered += 1
    db.commit()
    return recovered


def append_job_log(db: Session, job: Job, level: str, message: str, context: dict) -> JobLog:
    log = JobLog(job_id=job.id, level=level, message=message, context=context)
    db.add(log)
    return log


def _latest_running_execution(db: Session, job_id: str, worker_id: str) -> JobExecution | None:
    return db.execute(
        select(JobExecution)
        .where(
            JobExecution.job_id == job_id,
            JobExecution.worker_id == worker_id,
            JobExecution.status == ExecutionStatus.RUNNING,
        )
        .order_by(JobExecution.started_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def _duration_ms(started_at: datetime, completed_at: datetime) -> int:
    return int((completed_at - started_at).total_seconds() * 1000)


def _job_retry_policy(db: Session, job: Job) -> RetryPolicy | None:
    if job.retry_policy_id:
        return db.get(RetryPolicy, job.retry_policy_id)
    return db.get(RetryPolicy, job.queue.retry_policy_id) if job.queue.retry_policy_id else None
