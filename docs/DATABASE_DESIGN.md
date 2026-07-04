# Database Design

## Core Tables

- `users`: Auth identities with unique email and PBKDF2 password hashes.
- `organizations`: Top-level ownership boundary.
- `projects`: Isolation boundary for queues, jobs, retry policies, and membership.
- `project_members`: Role mapping between users and projects.
- `retry_policies`: Fixed, linear, or exponential retry configuration.
- `queues`: Processing lanes with priority, max concurrency, retry policy, and pause/resume status.
- `jobs`: Main lifecycle table with payload, metadata, priority, schedule, attempts, locks, and timestamps.
- `job_executions`: Attempt history for every run.
- `job_logs`: Structured audit trail for creation, claim, start, completion, retry, and DLQ transitions.
- `workers`: Worker registry and latest heartbeat.
- `worker_heartbeats`: Historical heartbeat samples for observability.
- `dead_letter_entries`: Permanent failure records with payload snapshot and final error.

## Important Indexes

- `users.email`: Fast login lookup.
- `organizations.slug`: Stable URL-safe organization identity.
- `projects.organization_id + slug`: Organization-scoped project lookup.
- `queues.project_id + status + priority`: Queue listing and scheduler scans.
- `jobs.status + scheduled_at + priority + created_at`: Claim scan ordering.
- `jobs.queue_id + status`: Queue health and backlog metrics.
- `jobs.project_id + idempotency_key`: Idempotent job creation.
- `worker_heartbeats.worker_id + recorded_at`: Worker monitoring.
- `job_logs.job_id + created_at`: Job timeline.

## Cascading Behavior

- Deleting an organization deletes its projects.
- Deleting a project deletes queues, retry policies, memberships, and jobs.
- Deleting a queue deletes its jobs.
- Deleting a job deletes executions and logs.
- Worker references on jobs/executions are set to null where historical preservation is preferred.

## Performance Considerations

The claim query is designed for a high-write table:

1. Filter by status and scheduled time.
2. Exclude paused queues.
3. Respect queue concurrency by counting active jobs for the queue.
4. Order by job priority, queue priority, scheduled time, and creation time.
5. Transition `queued -> claimed` with a guarded update.

For larger deployments, the next optimization would be partitioning `jobs` by project or queue, adding a partial index for claimable jobs, and moving high-volume logs to a time-series or append-optimized store.

