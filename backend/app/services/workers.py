from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Worker, WorkerHeartbeat, WorkerStatus


def register_worker(
    db: Session,
    *,
    worker_id: str,
    hostname: str,
    queues: list[str],
    version: str,
) -> Worker:
    now = datetime.utcnow()
    worker = db.get(Worker, worker_id)
    if worker is None:
        worker = Worker(
            id=worker_id,
            hostname=hostname,
            queues=queues,
            version=version,
            status=WorkerStatus.ONLINE,
            started_at=now,
            last_heartbeat_at=now,
        )
        db.add(worker)
    else:
        worker.hostname = hostname
        worker.queues = queues
        worker.version = version
        worker.status = WorkerStatus.ONLINE
        worker.started_at = now
        worker.last_heartbeat_at = now
    db.commit()
    db.refresh(worker)
    return worker


def heartbeat_worker(
    db: Session,
    *,
    worker_id: str,
    active_jobs: int,
    cpu_percent: int | None = None,
    memory_mb: int | None = None,
) -> Worker:
    now = datetime.utcnow()
    worker = db.get(Worker, worker_id)
    if worker is None:
        worker = Worker(
            id=worker_id,
            hostname="unknown",
            queues=[],
            status=WorkerStatus.ONLINE,
            active_jobs=active_jobs,
            last_heartbeat_at=now,
        )
        db.add(worker)
    worker.active_jobs = active_jobs
    worker.last_heartbeat_at = now
    worker.status = WorkerStatus.ONLINE
    db.add(
        WorkerHeartbeat(
            worker_id=worker_id,
            active_jobs=active_jobs,
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            recorded_at=now,
        )
    )
    db.commit()
    db.refresh(worker)
    return worker


def mark_stale_workers_offline(db: Session, stale_before: datetime) -> int:
    workers = db.execute(
        select(Worker).where(
            Worker.last_heartbeat_at < stale_before,
            Worker.status != WorkerStatus.OFFLINE,
        )
    ).scalars()
    count = 0
    for worker in workers:
        worker.status = WorkerStatus.OFFLINE
        count += 1
    db.commit()
    return count


def update_worker_status(db: Session, worker_id: str, status: WorkerStatus) -> Worker | None:
    worker = db.get(Worker, worker_id)
    if worker:
        worker.status = status
        db.commit()
        db.refresh(worker)
    return worker


