from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "backend"))

from app.auth.security import hash_password
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models import MemberRole, Organization, Project, ProjectMember, Queue, RetryPolicy, User, Worker
from app.models.enums import RetryStrategy, WorkerStatus
from app.schemas.job import JobCreate
from app.services.jobs import create_job


def main() -> None:
    init_db()
    with SessionLocal() as db:
        user = db.query(User).filter_by(email="demo@pulsequeue.local").one_or_none()
        if user is None:
            user = User(
                email="demo@pulsequeue.local",
                full_name="PulseQueue Demo",
                password_hash=hash_password("password123"),
            )
            db.add(user)
            db.flush()
        organization = db.query(Organization).filter_by(slug="acme-platform").one_or_none()
        if organization is None:
            organization = Organization(name="Acme Platform", slug="acme-platform", owner_id=user.id)
            db.add(organization)
            db.flush()
        project = db.query(Project).filter_by(organization_id=organization.id, slug="payment-processing").one_or_none()
        if project is None:
            project = Project(
                organization_id=organization.id,
                name="Payment Processing",
                slug="payment-processing",
                description="Critical payment and notification background jobs.",
            )
            db.add(project)
            db.flush()
            db.add(ProjectMember(project_id=project.id, user_id=user.id, role=MemberRole.OWNER))
        policy = db.query(RetryPolicy).filter_by(project_id=project.id, name="default-exponential").one_or_none()
        if policy is None:
            policy = RetryPolicy(
                project_id=project.id,
                name="default-exponential",
                strategy=RetryStrategy.EXPONENTIAL,
                max_attempts=3,
                delay_seconds=15,
                max_delay_seconds=600,
            )
            db.add(policy)
            db.flush()
        queue_names = [
            ("payment-settlement", "Payment capture, settlement, and reconciliation", 100, 8),
            ("email-critical", "Transactional email and notification delivery", 90, 12),
            ("monthly-reports", "Scheduled report generation", 35, 2),
        ]
        queues = []
        for name, description, priority, concurrency in queue_names:
            queue = db.query(Queue).filter_by(project_id=project.id, name=name).one_or_none()
            if queue is None:
                queue = Queue(
                    project_id=project.id,
                    retry_policy_id=policy.id,
                    name=name,
                    description=description,
                    priority=priority,
                    max_concurrency=concurrency,
                    created_by_id=user.id,
                )
                db.add(queue)
                db.flush()
            queues.append(queue)
        worker = db.get(Worker, "worker-demo-1")
        if worker is None:
            db.add(
                Worker(
                    id="worker-demo-1",
                    hostname="demo-host",
                    queues=[queue.id for queue in queues],
                    status=WorkerStatus.ONLINE,
                    version="demo",
                )
            )
        db.commit()

        existing_jobs = db.query(Queue).join(Queue.jobs).filter(Queue.project_id == project.id).count()
        if existing_jobs == 0:
            create_job(
                db,
                JobCreate(
                    queue_id=queues[0].id,
                    payload={"action": "echo", "operation": "capture-payment"},
                    tags=["payments", "critical"],
                    priority=100,
                ),
            )
            create_job(
                db,
                JobCreate(
                    queue_id=queues[1].id,
                    payload={"action": "sleep", "seconds": 2},
                    tags=["email"],
                    priority=70,
                ),
            )
            create_job(
                db,
                JobCreate(
                    queue_id=queues[2].id,
                    payload={"action": "fail", "message": "Renderer timed out"},
                    tags=["reports", "retry-demo"],
                    priority=20,
                ),
            )

        print("Demo data ready")
        print("Email: demo@pulsequeue.local")
        print("Password: password123")
        print(f"Project ID: {project.id}")


if __name__ == "__main__":
    main()

