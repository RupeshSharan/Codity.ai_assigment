from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models import JobKind, JobStatus
from app.schemas.common import ORMModel, Timestamped


class JobPayloadBase(BaseModel):
    kind: JobKind = JobKind.IMMEDIATE
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    priority: int = Field(default=0, ge=0, le=1000)
    scheduled_at: datetime | None = None
    delay_seconds: int | None = Field(default=None, ge=0, le=604_800)
    timeout_seconds: int = Field(default=300, ge=1, le=86_400)
    cron_expression: str | None = None
    batch_id: str | None = None
    idempotency_key: str | None = None
    retry_policy_id: str | None = None
    max_attempts: int | None = Field(default=None, ge=1, le=25)


class JobCreate(JobPayloadBase):
    queue_id: str


class BatchJobItem(JobPayloadBase):
    pass


class BatchJobCreate(BaseModel):
    queue_id: str
    jobs: list[BatchJobItem] = Field(min_length=1, max_length=1000)
    batch_id: str | None = None


class JobRead(Timestamped):
    id: str
    project_id: str
    queue_id: str
    retry_policy_id: str | None
    batch_id: str | None
    kind: JobKind
    status: JobStatus
    payload: dict[str, Any]
    job_metadata: dict[str, Any]
    tags: list
    priority: int
    retry_count: int
    timeout_seconds: int
    cron_expression: str | None
    idempotency_key: str | None
    scheduled_at: datetime
    claimed_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    failed_at: datetime | None
    locked_by_worker_id: str | None
    last_error: str | None


class JobFilter(BaseModel):
    project_id: str | None = None
    queue_id: str | None = None
    worker_id: str | None = None
    status: JobStatus | None = None
    tag: str | None = None
    limit: int = Field(default=25, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class JobExecutionRead(ORMModel):
    id: str
    job_id: str
    worker_id: str | None
    attempt_number: int
    status: str
    started_at: datetime
    completed_at: datetime | None
    duration_ms: int | None
    error: str | None
    result: dict[str, Any] | None


class JobLogRead(ORMModel):
    id: str
    job_id: str
    execution_id: str | None
    level: str
    message: str
    context: dict[str, Any]
    created_at: datetime


class JobDetail(BaseModel):
    job: JobRead
    executions: list[JobExecutionRead]
    logs: list[JobLogRead]


class JobCompletionRequest(BaseModel):
    result: dict[str, Any] = Field(default_factory=dict)


class JobFailureRequest(BaseModel):
    error: str
