from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
import json
import logging
import os
import socket
import time

import signal
from app.auth.security import new_worker_id
from app.db.session import SessionLocal
from app.models import Job, WorkerStatus
from app.services.jobs import claim_next_job, complete_job, fail_job, start_job
from app.services.workers import heartbeat_worker, register_worker, update_worker_status

logger = logging.getLogger(__name__)


@dataclass
class WorkerConfig:
    worker_id: str
    hostname: str
    queues: list[str]
    concurrency: int = 4
    poll_interval_seconds: float = 1.0
    version: str = "dev"


class WorkerRunner:
    def __init__(self, config: WorkerConfig):
        self.config = config
        self._active_jobs = 0
        self._stopping = False

    def start(self) -> None:
        def handle_signal(signum, frame):
            logger.info("Signal %d received. Graceful shutdown initiated...", signum)
            self.stop()

        try:
            signal.signal(signal.SIGINT, handle_signal)
            signal.signal(signal.SIGTERM, handle_signal)
        except ValueError:
            # Signal registration might fail if run in a sub-thread in testing environments
            pass

        with SessionLocal() as db:
            register_worker(
                db,
                worker_id=self.config.worker_id,
                hostname=self.config.hostname,
                queues=self.config.queues,
                version=self.config.version,
            )
        logger.info("Worker %s started with concurrency=%s", self.config.worker_id, self.config.concurrency)
        with ThreadPoolExecutor(max_workers=self.config.concurrency) as executor:
            while not self._stopping:
                self._send_heartbeat()
                if self._active_jobs >= self.config.concurrency:
                    time.sleep(self.config.poll_interval_seconds)
                    continue
                with SessionLocal() as db:
                    job = claim_next_job(
                        db,
                        worker_id=self.config.worker_id,
                        queue_ids=self.config.queues or None,
                    )
                if job is None:
                    time.sleep(self.config.poll_interval_seconds)
                    continue
                self._active_jobs += 1
                executor.submit(self._execute_claimed_job, job.id)
        
        logger.info("All active jobs completed. Worker %s shutting down. Setting status to OFFLINE.", self.config.worker_id)
        with SessionLocal() as db:
            update_worker_status(db, worker_id=self.config.worker_id, status=WorkerStatus.OFFLINE)

    def stop(self) -> None:
        self._stopping = True
        logger.info("Draining active jobs. Worker status set to DRAINING.")
        with SessionLocal() as db:
            update_worker_status(db, worker_id=self.config.worker_id, status=WorkerStatus.DRAINING)

    def _send_heartbeat(self) -> None:
        with SessionLocal() as db:
            heartbeat_worker(db, worker_id=self.config.worker_id, active_jobs=self._active_jobs)

    def _execute_claimed_job(self, job_id: str) -> None:
        try:
            with SessionLocal() as db:
                start_job(db, job_id, self.config.worker_id)
            result = execute_payload(job_id)
            with SessionLocal() as db:
                complete_job(db, job_id, self.config.worker_id, result)
        except Exception as exc:
            logger.exception("Job %s failed.", job_id)
            with SessionLocal() as db:
                fail_job(db, job_id, self.config.worker_id, str(exc))
        finally:
            self._active_jobs = max(0, self._active_jobs - 1)
            self._send_heartbeat()


def execute_payload(job_id: str) -> dict:
    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if job is None:
            raise RuntimeError(f"Job {job_id} disappeared before execution.")
        payload = job.payload or {}
    action = payload.get("action", "echo")
    if action == "sleep":
        time.sleep(float(payload.get("seconds", 1)))
        return {"slept_seconds": payload.get("seconds", 1), "completed_at": datetime.utcnow().isoformat()}
    if action == "fail":
        raise RuntimeError(payload.get("message", "Intentional failure requested by payload."))
    return {"echo": payload, "completed_at": datetime.utcnow().isoformat()}


def worker_config_from_env() -> WorkerConfig:
    queues = [item.strip() for item in os.getenv("WORKER_QUEUE_IDS", "").split(",") if item.strip()]
    return WorkerConfig(
        worker_id=os.getenv("WORKER_ID", new_worker_id()),
        hostname=os.getenv("WORKER_HOSTNAME", socket.gethostname()),
        queues=queues,
        concurrency=int(os.getenv("WORKER_CONCURRENCY", "4")),
        poll_interval_seconds=float(os.getenv("WORKER_POLL_INTERVAL_SECONDS", "1")),
        version=os.getenv("WORKER_VERSION", "dev"),
    )


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    WorkerRunner(worker_config_from_env()).start()

