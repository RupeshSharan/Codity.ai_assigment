# Design Decisions

## Backend First, Feature Count Second

The assignment prioritizes engineering quality. PulseQueue therefore implements reliability-critical backend paths before bonus features. This makes the submission stronger because the core scheduler story can be defended in code and tests.

## Database as Source of Truth

PostgreSQL is the primary consistency layer. Redis is included for future distributed locks, rate limiting, and cache work, but the current claim path intentionally relies on database transactions so job ownership survives process restarts.

## Atomic Claiming Strategy

Workers never claim jobs by reading and then blindly updating. The service filters eligible jobs and transitions status with a guarded write. PostgreSQL deployments can use `SKIP LOCKED`; SQLite tests use a guarded update to prove duplicate claims are prevented.

## Retry Policies Are Data

Retry behavior lives in `retry_policies`, not hard-coded worker logic. Jobs can inherit from queue policy or override policy/max attempts. This supports fixed, linear, and exponential backoff.

## Execution History Is Separate From Job State

`jobs` stores current state. `job_executions` and `job_logs` store history. This keeps dashboard queries simple while preserving auditability.

## Worker Control Plane

Worker routes are intentionally separate from user routes. In a production version, they should use a service token or mTLS. The assignment version keeps them simple and visible so the lifecycle is easy to test.

## Dashboard Shape

The dashboard is an operations console, not a landing page. It surfaces backlog, failures, workers, throughput, queue controls, and job explorer state immediately.

