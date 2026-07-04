from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ExecutionStatus, Job, JobExecution, JobStatus, Queue, QueueStatus, Worker, WorkerStatus


def overview_metrics(db: Session) -> dict:
    counts = dict(
        db.execute(select(Job.status, func.count(Job.id)).group_by(Job.status)).all()
    )
    total_failures = counts.get(JobStatus.DEAD_LETTER, 0) + counts.get(JobStatus.FAILED, 0)
    completed = counts.get(JobStatus.COMPLETED, 0)
    attempts = completed + total_failures
    average_execution_ms = db.execute(
        select(func.avg(JobExecution.duration_ms)).where(JobExecution.status == ExecutionStatus.SUCCEEDED)
    ).scalar()
    queue_health = dict(
        db.execute(
            select(Queue.status, func.count(Queue.id)).group_by(Queue.status)
        ).all()
    )
    workers_online = db.execute(
        select(func.count(Worker.id)).where(Worker.status == WorkerStatus.ONLINE)
    ).scalar_one()
    return {
        "running_jobs": counts.get(JobStatus.RUNNING, 0) + counts.get(JobStatus.CLAIMED, 0),
        "queued_jobs": counts.get(JobStatus.QUEUED, 0) + counts.get(JobStatus.SCHEDULED, 0),
        "failed_jobs": total_failures,
        "completed_jobs": completed,
        "workers_online": workers_online,
        "queue_health": {
            "active": queue_health.get(QueueStatus.ACTIVE, 0),
            "paused": queue_health.get(QueueStatus.PAUSED, 0),
        },
        "retry_rate_percent": round((total_failures / attempts) * 100, 2) if attempts else 0.0,
        "average_execution_ms": int(average_execution_ms) if average_execution_ms else None,
    }


def queue_stats(db: Session, queue_id: str) -> dict:
    counts = dict(
        db.execute(
            select(Job.status, func.count(Job.id)).where(Job.queue_id == queue_id).group_by(Job.status)
        ).all()
    )
    waits = db.execute(
        select(Job.created_at, Job.claimed_at).where(
            Job.queue_id == queue_id,
            Job.claimed_at.is_not(None),
        )
    ).all()
    avg_wait = (
        sum((claimed - created).total_seconds() * 1000 for created, claimed in waits) / len(waits)
        if waits
        else None
    )
    return {
        "queue_id": queue_id,
        "queued": counts.get(JobStatus.QUEUED, 0),
        "scheduled": counts.get(JobStatus.SCHEDULED, 0),
        "running": counts.get(JobStatus.RUNNING, 0) + counts.get(JobStatus.CLAIMED, 0),
        "completed": counts.get(JobStatus.COMPLETED, 0),
        "failed": counts.get(JobStatus.FAILED, 0),
        "dead_letter": counts.get(JobStatus.DEAD_LETTER, 0),
        "average_wait_ms": int(avg_wait) if avg_wait else None,
    }
