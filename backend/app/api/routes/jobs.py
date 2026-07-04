from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import get_current_user, require_project_role
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models import DeadLetterEntry, Job, MemberRole, ProjectMember, Queue, User
from app.models.enums import JobStatus
from app.schemas.common import PaginatedResponse
from app.schemas.job import BatchJobCreate, JobCreate, JobDetail, JobFilter, JobRead
from app.services.jobs import create_batch, create_job, retry_dead_letter_job

router = APIRouter()


@router.post("", response_model=JobRead, status_code=201)
def submit_job(
    payload: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Job:
    queue = _queue_for_write(db, payload.queue_id, current_user)
    return create_job(db, payload)


@router.post("/batch", response_model=list[JobRead], status_code=201)
def submit_batch(
    payload: BatchJobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Job]:
    _queue_for_write(db, payload.queue_id, current_user)
    return create_batch(db, payload)


@router.get("", response_model=PaginatedResponse)
def list_jobs(
    project_id: str | None = None,
    queue_id: str | None = None,
    worker_id: str | None = None,
    status: JobStatus | None = None,
    tag: str | None = None,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    stmt = select(Job)
    count_stmt = select(func.count(Job.id))
    filters = []
    if queue_id:
        queue = db.get(Queue, queue_id)
        if queue is None:
            raise NotFoundError("Queue not found.")
        require_project_role(db, current_user, queue.project_id, set(MemberRole))
        filters.append(Job.queue_id == queue_id)
    elif project_id:
        require_project_role(db, current_user, project_id, set(MemberRole))
        filters.append(Job.project_id == project_id)
    else:
        memberships = select(ProjectMember.project_id).where(ProjectMember.user_id == current_user.id)
        filters.append(Job.project_id.in_(memberships))
    if worker_id:
        filters.append(Job.locked_by_worker_id == worker_id)
    if status:
        filters.append(Job.status == status)
    if filters:
        stmt = stmt.where(*filters)
        count_stmt = count_stmt.where(*filters)
    if tag:
        jobs = [job for job in db.execute(stmt.order_by(Job.created_at.desc())).scalars() if tag in job.tags]
        total = len(jobs)
        return {"items": jobs[offset : offset + limit], "total": total, "limit": limit, "offset": offset}
    total = db.execute(count_stmt).scalar_one()
    items = list(db.execute(stmt.order_by(Job.created_at.desc()).offset(offset).limit(limit)).scalars())
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/dead-letter/list", response_model=list[JobRead])
def list_dead_letter_jobs(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Job]:
    require_project_role(db, current_user, project_id, set(MemberRole))
    return list(
        db.execute(
            select(Job)
            .join(DeadLetterEntry)
            .where(Job.project_id == project_id, Job.status == JobStatus.DEAD_LETTER)
            .order_by(DeadLetterEntry.created_at.desc())
        ).scalars()
    )


@router.get("/{job_id}", response_model=JobDetail)
def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    job = db.execute(
        select(Job)
        .where(Job.id == job_id)
        .options(selectinload(Job.executions), selectinload(Job.logs))
    ).scalar_one_or_none()
    if job is None:
        raise NotFoundError("Job not found.")
    require_project_role(db, current_user, job.project_id, set(MemberRole))
    return {
        "job": job,
        "executions": sorted(job.executions, key=lambda item: item.started_at),
        "logs": sorted(job.logs, key=lambda item: item.created_at),
    }


@router.post("/{job_id}/retry", response_model=JobRead)
def retry_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise NotFoundError("Job not found.")
    require_project_role(db, current_user, job.project_id, {MemberRole.OWNER, MemberRole.ADMIN, MemberRole.DEVELOPER})
    return retry_dead_letter_job(db, job_id)


def _queue_for_write(db: Session, queue_id: str, user: User) -> Queue:
    queue = db.get(Queue, queue_id)
    if queue is None:
        raise NotFoundError("Queue not found.")
    require_project_role(db, user, queue.project_id, {MemberRole.OWNER, MemberRole.ADMIN, MemberRole.DEVELOPER})
    return queue
