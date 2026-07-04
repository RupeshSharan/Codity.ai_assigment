from datetime import datetime

from pydantic import BaseModel, Field

from app.models import WorkerStatus
from app.schemas.common import Timestamped
from app.schemas.job import JobRead


class WorkerRegisterRequest(BaseModel):
    worker_id: str | None = None
    hostname: str = Field(min_length=1, max_length=255)
    queues: list[str] = Field(default_factory=list)
    version: str = "dev"


class WorkerHeartbeatRequest(BaseModel):
    active_jobs: int = Field(default=0, ge=0)
    cpu_percent: int | None = Field(default=None, ge=0, le=100)
    memory_mb: int | None = Field(default=None, ge=0)


class WorkerRead(Timestamped):
    id: str
    hostname: str
    queues: list
    status: WorkerStatus
    active_jobs: int
    version: str
    started_at: datetime
    last_heartbeat_at: datetime


class ClaimRequest(BaseModel):
    queue_ids: list[str] = Field(default_factory=list)


class ClaimResponse(BaseModel):
    job: JobRead | None

