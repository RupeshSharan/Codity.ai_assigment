from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from sqlalchemy.orm import Session, sessionmaker

from app.models import Job, Worker
from app.models.enums import JobStatus, WorkerStatus
from app.schemas.job import JobCreate
from app.services.jobs import claim_next_job, create_job


def test_claim_next_job_marks_job_claimed(db_session: Session, seeded) -> None:
    job = create_job(db_session, JobCreate(queue_id=seeded.queue.id, payload={"action": "echo"}, priority=50))

    claimed = claim_next_job(db_session, worker_id=seeded.worker.id, now=datetime.utcnow())

    assert claimed is not None
    assert claimed.id == job.id
    assert claimed.status == JobStatus.CLAIMED
    assert claimed.locked_by_worker_id == seeded.worker.id
    assert claimed.claimed_at is not None


def test_atomic_claim_prevents_duplicate_execution(db_session: Session, seeded) -> None:
    create_job(db_session, JobCreate(queue_id=seeded.queue.id, payload={"action": "echo"}, priority=50))
    engine = db_session.bind
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)

    with TestingSession() as db:
        db.add(Worker(id="worker-test-2", hostname="test-host-2", queues=[seeded.queue.id], status=WorkerStatus.ONLINE))
        db.commit()

    def claim(worker_id: str) -> str | None:
        with TestingSession() as db:
            job = claim_next_job(db, worker_id=worker_id, now=datetime.utcnow())
            return job.id if job else None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(claim, ["worker-test-1", "worker-test-2"]))

    claimed_ids = [item for item in results if item]
    assert len(claimed_ids) == 1
    assert len(set(claimed_ids)) == 1

    with TestingSession() as db:
        jobs = list(db.query(Job).all())
        assert len(jobs) == 1
        assert jobs[0].status == JobStatus.CLAIMED

