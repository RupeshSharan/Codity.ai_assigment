# Testing

Run backend tests:

```bash
cd backend
python -m pytest -q
```

Current critical coverage:

- Atomic claiming prevents duplicate execution.
- Jobs transition through retry and Dead Letter Queue behavior.
- Fixed, linear, and exponential retry delays.

Recommended next tests:

- API authentication and authorization.
- Queue pause/resume behavior.
- Scheduler stale-worker recovery.
- PostgreSQL `SKIP LOCKED` integration.
- Worker graceful shutdown.

