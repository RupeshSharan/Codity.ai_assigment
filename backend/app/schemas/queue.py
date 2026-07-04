from pydantic import BaseModel, Field

from app.models import QueueStatus, RetryStrategy
from app.schemas.common import Timestamped


class RetryPolicyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    max_attempts: int = Field(default=3, ge=1, le=25)
    delay_seconds: int = Field(default=30, ge=0, le=86_400)
    max_delay_seconds: int = Field(default=3600, ge=1, le=604_800)
    jitter_seconds: int = Field(default=0, ge=0, le=3600)


class RetryPolicyRead(Timestamped):
    id: str
    project_id: str
    name: str
    strategy: RetryStrategy
    max_attempts: int
    delay_seconds: int
    max_delay_seconds: int
    jitter_seconds: int


class QueueCreate(BaseModel):
    project_id: str
    retry_policy_id: str | None = None
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None
    priority: int = Field(default=0, ge=0, le=100)
    max_concurrency: int = Field(default=5, ge=1, le=500)


class QueueUpdate(BaseModel):
    description: str | None = None
    priority: int | None = Field(default=None, ge=0, le=100)
    max_concurrency: int | None = Field(default=None, ge=1, le=500)
    retry_policy_id: str | None = None


class QueueRead(Timestamped):
    id: str
    project_id: str
    retry_policy_id: str | None
    name: str
    description: str | None
    priority: int
    max_concurrency: int
    status: QueueStatus


class QueueStats(BaseModel):
    queue_id: str
    queued: int
    scheduled: int
    running: int
    completed: int
    failed: int
    dead_letter: int
    average_wait_ms: int | None

