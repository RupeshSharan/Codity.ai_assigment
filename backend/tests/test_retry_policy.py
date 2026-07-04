from app.models import RetryPolicy
from app.models.enums import RetryStrategy
from app.services.retry import retry_delay_seconds


def test_retry_delay_strategies() -> None:
    fixed = RetryPolicy(strategy=RetryStrategy.FIXED, delay_seconds=10, max_delay_seconds=100, jitter_seconds=0)
    linear = RetryPolicy(strategy=RetryStrategy.LINEAR, delay_seconds=10, max_delay_seconds=100, jitter_seconds=0)
    exponential = RetryPolicy(strategy=RetryStrategy.EXPONENTIAL, delay_seconds=10, max_delay_seconds=100, jitter_seconds=0)

    assert retry_delay_seconds(fixed, 3) == 10
    assert retry_delay_seconds(linear, 3) == 30
    assert retry_delay_seconds(exponential, 3) == 40

