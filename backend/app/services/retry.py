from datetime import datetime, timedelta
import random

from app.models import RetryPolicy, RetryStrategy


def retry_delay_seconds(policy: RetryPolicy, next_attempt_number: int) -> int:
    base = policy.delay_seconds
    if policy.strategy == RetryStrategy.FIXED:
        delay = base
    elif policy.strategy == RetryStrategy.LINEAR:
        delay = base * next_attempt_number
    else:
        delay = base * (2 ** max(next_attempt_number - 1, 0))
    if policy.jitter_seconds:
        delay += random.randint(0, policy.jitter_seconds)
    return min(delay, policy.max_delay_seconds)


def next_retry_time(policy: RetryPolicy, next_attempt_number: int, now: datetime | None = None) -> datetime:
    current = now or datetime.utcnow()
    return current + timedelta(seconds=retry_delay_seconds(policy, next_attempt_number))

