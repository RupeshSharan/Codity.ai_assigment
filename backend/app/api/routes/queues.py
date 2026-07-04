from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_project_role
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models import MemberRole, Project, Queue, QueueStatus, RetryPolicy, User
from app.schemas.queue import (
    QueueCreate,
    QueueRead,
    QueueStats,
    QueueUpdate,
    RetryPolicyCreate,
    RetryPolicyRead,
)
from app.services.metrics import queue_stats

router = APIRouter()


@router.post("/retry-policies/{project_id}", response_model=RetryPolicyRead, status_code=201)
def create_retry_policy(
    project_id: str,
    payload: RetryPolicyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RetryPolicy:
    require_project_role(db, current_user, project_id, {MemberRole.OWNER, MemberRole.ADMIN, MemberRole.DEVELOPER})
    policy = RetryPolicy(project_id=project_id, **payload.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


@router.get("/retry-policies/{project_id}", response_model=list[RetryPolicyRead])
def list_retry_policies(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RetryPolicy]:
    require_project_role(db, current_user, project_id, set(MemberRole))
    return list(db.execute(select(RetryPolicy).where(RetryPolicy.project_id == project_id)).scalars())


@router.post("", response_model=QueueRead, status_code=201)
def create_queue(
    payload: QueueCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Queue:
    require_project_role(db, current_user, payload.project_id, {MemberRole.OWNER, MemberRole.ADMIN, MemberRole.DEVELOPER})
    if payload.retry_policy_id and db.get(RetryPolicy, payload.retry_policy_id) is None:
        raise NotFoundError("Retry policy not found.")
    queue = Queue(**payload.model_dump(), created_by_id=current_user.id)
    db.add(queue)
    db.commit()
    db.refresh(queue)
    return queue


@router.get("", response_model=list[QueueRead])
def list_queues(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Queue]:
    require_project_role(db, current_user, project_id, set(MemberRole))
    return list(
        db.execute(
            select(Queue).where(Queue.project_id == project_id).order_by(Queue.priority.desc(), Queue.name)
        ).scalars()
    )


@router.patch("/{queue_id}", response_model=QueueRead)
def update_queue(
    queue_id: str,
    payload: QueueUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Queue:
    queue = _queue_for_user(db, queue_id, current_user, write=True)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(queue, key, value)
    db.commit()
    db.refresh(queue)
    return queue


@router.post("/{queue_id}/pause", response_model=QueueRead)
def pause_queue(
    queue_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Queue:
    queue = _queue_for_user(db, queue_id, current_user, write=True)
    queue.status = QueueStatus.PAUSED
    db.commit()
    db.refresh(queue)
    return queue


@router.post("/{queue_id}/resume", response_model=QueueRead)
def resume_queue(
    queue_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Queue:
    queue = _queue_for_user(db, queue_id, current_user, write=True)
    queue.status = QueueStatus.ACTIVE
    db.commit()
    db.refresh(queue)
    return queue


@router.get("/{queue_id}/stats", response_model=QueueStats)
def get_queue_stats(
    queue_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    queue = _queue_for_user(db, queue_id, current_user)
    return queue_stats(db, queue.id)


def _queue_for_user(db: Session, queue_id: str, user: User, write: bool = False) -> Queue:
    queue = db.get(Queue, queue_id)
    if queue is None:
        raise NotFoundError("Queue not found.")
    allowed = {MemberRole.OWNER, MemberRole.ADMIN, MemberRole.DEVELOPER} if write else set(MemberRole)
    require_project_role(db, user, queue.project_id, allowed)
    return queue

