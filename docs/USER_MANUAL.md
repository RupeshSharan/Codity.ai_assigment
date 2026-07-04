# User Manual

## 1. Register and Login

Use `/api/v1/auth/register` to create a user and organization. Use `/api/v1/auth/login` to receive a bearer token. Include the token in dashboard/API calls:

```text
Authorization: Bearer <token>
```

## 2. Create Project

Create a project under an organization. Projects isolate queues, jobs, retry policies, members, and metrics.

## 3. Configure Retry Policy

Create one or more retry policies:

- `fixed`: same delay between attempts.
- `linear`: delay grows by attempt number.
- `exponential`: delay doubles each attempt up to a maximum.

## 4. Create Queue

Queues define independent processing lanes with priority, max concurrency, retry policy, and pause/resume status.

## 5. Submit Jobs

Submit:

- Immediate jobs by omitting `scheduled_at`.
- Delayed jobs with `delay_seconds`.
- Scheduled jobs with `scheduled_at`.
- Recurring jobs with `cron_expression`.
- Batch jobs through `/api/v1/jobs/batch`.

Payload examples:

```json
{"action": "echo", "message": "hello"}
```

```json
{"action": "sleep", "seconds": 2}
```

```json
{"action": "fail", "message": "simulate retry"}
```

## 6. Run Workers

Workers register, heartbeat, claim, start, complete, and fail jobs. The local worker runner executes demo payload actions.

## 7. Monitor Operations

Use the dashboard to inspect:

- Running, queued, failed, and completed jobs.
- Worker status and heartbeat freshness.
- Queue status, priority, and concurrency.
- Dead Letter Queue jobs.
- Throughput and retry rate.

## 8. Recover Failures

The scheduler promotes due jobs and recovers stale worker claims. Dead-letter jobs can be retried through `/api/v1/jobs/{job_id}/retry`.

