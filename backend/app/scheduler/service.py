from datetime import datetime, timedelta
import logging
import time

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.jobs import promote_due_scheduled_jobs, recover_stale_jobs
from app.services.workers import mark_stale_workers_offline

logger = logging.getLogger(__name__)


def scheduler_tick(db: Session) -> dict[str, int]:
    settings = get_settings()
    now = datetime.utcnow()
    stale_before = now - timedelta(seconds=settings.worker_heartbeat_timeout_seconds)
    promoted = promote_due_scheduled_jobs(db, now)
    recovered = recover_stale_jobs(db, stale_before)
    offline = mark_stale_workers_offline(db, stale_before)
    return {"promoted": promoted, "recovered": recovered, "offline_workers": offline}


def run_scheduler_forever(interval_seconds: int = 5) -> None:
    logger.info("Scheduler service started.")
    while True:
        with SessionLocal() as db:
            result = scheduler_tick(db)
            logger.info("Scheduler tick completed: %s", result)
        time.sleep(interval_seconds)


if __name__ == "__main__":
    run_scheduler_forever()

