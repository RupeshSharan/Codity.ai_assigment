from collections.abc import Generator
from dataclasses import dataclass

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.auth.security import hash_password
from app.db.session import Base
from app.models import MemberRole, Organization, Project, ProjectMember, Queue, RetryPolicy, User, Worker
from app.models.enums import RetryStrategy, WorkerStatus


@dataclass
class SeedData:
    user: User
    organization: Organization
    project: Project
    queue: Queue
    retry_policy: RetryPolicy
    worker: Worker


@pytest.fixture()
def db_session(tmp_path) -> Generator[Session, None, None]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pulsequeue-test.db'}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def seeded(db_session: Session) -> SeedData:
    user = User(email="engineer@example.com", full_name="Test Engineer", password_hash=hash_password("password123"))
    db_session.add(user)
    db_session.flush()
    organization = Organization(name="Acme", slug="acme", owner_id=user.id)
    db_session.add(organization)
    db_session.flush()
    project = Project(organization_id=organization.id, name="Payments", slug="payments")
    db_session.add(project)
    db_session.flush()
    db_session.add(ProjectMember(project_id=project.id, user_id=user.id, role=MemberRole.OWNER))
    retry_policy = RetryPolicy(
        project_id=project.id,
        name="fast-retry",
        strategy=RetryStrategy.EXPONENTIAL,
        max_attempts=2,
        delay_seconds=1,
        max_delay_seconds=30,
    )
    db_session.add(retry_policy)
    db_session.flush()
    queue = Queue(
        project_id=project.id,
        retry_policy_id=retry_policy.id,
        name="critical",
        priority=100,
        max_concurrency=1,
        created_by_id=user.id,
    )
    worker = Worker(
        id="worker-test-1",
        hostname="test-host",
        queues=[queue.id],
        status=WorkerStatus.ONLINE,
        version="test",
    )
    db_session.add_all([queue, worker])
    db_session.commit()
    return SeedData(
        user=user,
        organization=organization,
        project=project,
        queue=queue,
        retry_policy=retry_policy,
        worker=worker,
    )

