from pydantic import BaseModel


class OverviewMetrics(BaseModel):
    running_jobs: int
    queued_jobs: int
    failed_jobs: int
    completed_jobs: int
    workers_online: int
    queue_health: dict[str, int]
    retry_rate_percent: float
    average_execution_ms: int | None

