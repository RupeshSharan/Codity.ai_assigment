from datetime import datetime
import uuid

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import (
    ExecutionStatus,
    JobKind,
    JobStatus,
    MemberRole,
    QueueStatus,
    RetryStrategy,
    WorkerStatus,
)


def uuid_str() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    owned_organizations: Mapped[list["Organization"]] = relationship(back_populates="owner")
    project_memberships: Mapped[list["ProjectMember"]] = relationship(back_populates="user")


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    owner: Mapped[User] = relationship(back_populates="owned_organizations")
    projects: Mapped[list["Project"]] = relationship(back_populates="organization", cascade="all, delete-orphan")


class Project(TimestampMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("organization_id", "slug", name="uq_project_org_slug"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    organization: Mapped[Organization] = relationship(back_populates="projects")
    members: Mapped[list["ProjectMember"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    queues: Mapped[list["Queue"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    retry_policies: Mapped[list["RetryPolicy"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class ProjectMember(TimestampMixin, Base):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_member"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[MemberRole] = mapped_column(Enum(MemberRole), default=MemberRole.DEVELOPER, nullable=False)

    project: Mapped[Project] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="project_memberships")


class RetryPolicy(TimestampMixin, Base):
    __tablename__ = "retry_policies"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_retry_policy_project_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    strategy: Mapped[RetryStrategy] = mapped_column(Enum(RetryStrategy), default=RetryStrategy.EXPONENTIAL)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    delay_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    max_delay_seconds: Mapped[int] = mapped_column(Integer, default=3600, nullable=False)
    jitter_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    project: Mapped[Project] = relationship(back_populates="retry_policies")
    queues: Mapped[list["Queue"]] = relationship(back_populates="retry_policy")
    jobs: Mapped[list["Job"]] = relationship(back_populates="retry_policy")


class Queue(TimestampMixin, Base):
    __tablename__ = "queues"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_queue_project_name"),
        Index("ix_queues_project_status_priority", "project_id", "status", "priority"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    retry_policy_id: Mapped[str | None] = mapped_column(ForeignKey("retry_policies.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_concurrency: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    status: Mapped[QueueStatus] = mapped_column(Enum(QueueStatus), default=QueueStatus.ACTIVE, nullable=False)
    created_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    project: Mapped[Project] = relationship(back_populates="queues")
    retry_policy: Mapped[RetryPolicy | None] = relationship(back_populates="queues")
    jobs: Mapped[list["Job"]] = relationship(back_populates="queue", cascade="all, delete-orphan")


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_claim_scan", "status", "scheduled_at", "priority", "created_at"),
        Index("ix_jobs_queue_status", "queue_id", "status"),
        Index("ix_jobs_idempotency", "project_id", "idempotency_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    queue_id: Mapped[str] = mapped_column(ForeignKey("queues.id", ondelete="CASCADE"), index=True)
    retry_policy_id: Mapped[str | None] = mapped_column(ForeignKey("retry_policies.id", ondelete="SET NULL"))
    batch_id: Mapped[str | None] = mapped_column(String(36), index=True)
    kind: Mapped[JobKind] = mapped_column(Enum(JobKind), default=JobKind.IMMEDIATE, nullable=False)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.QUEUED, index=True, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    job_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int | None] = mapped_column(Integer)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    cron_expression: Mapped[str | None] = mapped_column(String(120))
    idempotency_key: Mapped[str | None] = mapped_column(String(255))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime)
    locked_by_worker_id: Mapped[str | None] = mapped_column(ForeignKey("workers.id", ondelete="SET NULL"))
    last_error: Mapped[str | None] = mapped_column(Text)

    queue: Mapped[Queue] = relationship(back_populates="jobs")
    retry_policy: Mapped[RetryPolicy | None] = relationship(back_populates="jobs")
    executions: Mapped[list["JobExecution"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    logs: Mapped[list["JobLog"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    dead_letter_entry: Mapped["DeadLetterEntry | None"] = relationship(back_populates="job")


class Worker(TimestampMixin, Base):
    __tablename__ = "workers"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    queues: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[WorkerStatus] = mapped_column(Enum(WorkerStatus), default=WorkerStatus.ONLINE, nullable=False)
    active_jobs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="dev", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_heartbeat_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    executions: Mapped[list["JobExecution"]] = relationship(back_populates="worker")
    heartbeats: Mapped[list["WorkerHeartbeat"]] = relationship(back_populates="worker", cascade="all, delete-orphan")


class WorkerHeartbeat(Base):
    __tablename__ = "worker_heartbeats"
    __table_args__ = (Index("ix_worker_heartbeats_worker_recorded", "worker_id", "recorded_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    worker_id: Mapped[str] = mapped_column(ForeignKey("workers.id", ondelete="CASCADE"), index=True)
    active_jobs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cpu_percent: Mapped[int | None] = mapped_column(Integer)
    memory_mb: Mapped[int | None] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    worker: Mapped[Worker] = relationship(back_populates="heartbeats")


class JobExecution(Base):
    __tablename__ = "job_executions"
    __table_args__ = (Index("ix_job_executions_job_attempt", "job_id", "attempt_number"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    worker_id: Mapped[str | None] = mapped_column(ForeignKey("workers.id", ondelete="SET NULL"), index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ExecutionStatus] = mapped_column(Enum(ExecutionStatus), default=ExecutionStatus.RUNNING)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    result: Mapped[dict | None] = mapped_column(JSON)

    job: Mapped[Job] = relationship(back_populates="executions")
    worker: Mapped[Worker | None] = relationship(back_populates="executions")


class JobLog(Base):
    __tablename__ = "job_logs"
    __table_args__ = (Index("ix_job_logs_job_created", "job_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    execution_id: Mapped[str | None] = mapped_column(ForeignKey("job_executions.id", ondelete="SET NULL"))
    level: Mapped[str] = mapped_column(String(20), default="INFO", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    job: Mapped[Job] = relationship(back_populates="logs")


class DeadLetterEntry(Base):
    __tablename__ = "dead_letter_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, index=True)
    queue_id: Mapped[str] = mapped_column(ForeignKey("queues.id", ondelete="CASCADE"), index=True)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    retried_at: Mapped[datetime | None] = mapped_column(DateTime)

    job: Mapped[Job] = relationship(back_populates="dead_letter_entry")

