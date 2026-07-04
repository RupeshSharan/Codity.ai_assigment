from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import new_worker_id
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models import Worker
from app.schemas.job import JobCompletionRequest, JobFailureRequest, JobRead
from app.schemas.worker import (
    ClaimRequest,
    ClaimResponse,
    WorkerHeartbeatRequest,
    WorkerRead,
    WorkerRegisterRequest,
)
from app.services.jobs import claim_next_job, complete_job, fail_job, start_job
from app.services.workers import heartbeat_worker, register_worker

router = APIRouter()


@router.post("/register", response_model=WorkerRead, status_code=201)
def register(payload: WorkerRegisterRequest, db: Session = Depends(get_db)) -> Worker:
    worker_id = payload.worker_id or new_worker_id()
    return register_worker(
        db,
        worker_id=worker_id,
        hostname=payload.hostname,
        queues=payload.queues,
        version=payload.version,
    )


@router.get("", response_model=list[WorkerRead])
def list_workers(db: Session = Depends(get_db)) -> list[Worker]:
    return list(db.execute(select(Worker).order_by(Worker.last_heartbeat_at.desc())).scalars())


@router.post("/{worker_id}/heartbeat", response_model=WorkerRead)
def heartbeat(
    worker_id: str,
    payload: WorkerHeartbeatRequest,
    db: Session = Depends(get_db),
) -> Worker:
    return heartbeat_worker(
        db,
        worker_id=worker_id,
        active_jobs=payload.active_jobs,
        cpu_percent=payload.cpu_percent,
        memory_mb=payload.memory_mb,
    )


@router.post("/{worker_id}/claim", response_model=ClaimResponse)
def claim(
    worker_id: str,
    payload: ClaimRequest,
    db: Session = Depends(get_db),
) -> dict:
    job = claim_next_job(db, worker_id=worker_id, queue_ids=payload.queue_ids or None)
    return {"job": job}


@router.post("/{worker_id}/jobs/{job_id}/start")
def start(worker_id: str, job_id: str, db: Session = Depends(get_db)) -> dict:
    execution = start_job(db, job_id, worker_id)
    return {"execution_id": execution.id}


@router.post("/{worker_id}/jobs/{job_id}/complete", response_model=JobRead)
def complete(
    worker_id: str,
    job_id: str,
    payload: JobCompletionRequest,
    db: Session = Depends(get_db),
):
    return complete_job(db, job_id, worker_id, payload.result)


@router.post("/{worker_id}/jobs/{job_id}/fail", response_model=JobRead)
def fail(
    worker_id: str,
    job_id: str,
    payload: JobFailureRequest,
    db: Session = Depends(get_db),
):
    return fail_job(db, job_id, worker_id, payload.error)

