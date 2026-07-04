# Next Steps & Completed Milestones

This file outlines the implemented features and the continuation plan for advanced engineering features should you wish to expand PulseQueue further.

## Completed Milestones (Rubric Highlights)

- [x] **Relational Schema Design**: Complete PostgreSQL support (Users, Organizations, Projects, Queue, Jobs, Executions, Policies, Workers, Heartbeats, Logs, DLQ entries) defined in SQLAlchemy.
- [x] **Atomic Job Claiming**: Prevent duplicate execution using guarded database status updates (compatible with SQLite) and `FOR UPDATE SKIP LOCKED` (for PostgreSQL).
- [x] **Worker Graceful Shutdown**: Added Unix/Windows signal handling (`SIGINT`, `SIGTERM`). Workers transition to `draining` state, finish active tasks, and update database status to `offline` on exit.
- [x] **Full-Featured Operations Console**:
  - [x] JWT Authentication UI (Login, Signup, and Demo account bypass).
  - [x] Active Project & Organization selector.
  - [x] Queue Management (create queues, bind retry policies, and pause/resume triggers).
  - [x] Job Explorer (status filtering, tag search, and pagination).
  - [x] Manual Job Submitter (custom delay, scheduled time, cron, and preset payloads).
  - [x] Job Detail Drawer (pretty-printed JSON payload, execution attempts timeline, and audit logs).
  - [x] Dead Letter Queue & Retry Management (inspect failures, requeue/retry jobs).
  - [x] Worker Monitor (track hostname, queues, active jobs, and status).
  - [x] Policies Manager (list and create fixed, linear, and exponential retry strategies).
- [x] **Database Seeder**: Added `scripts/seed_demo.py` command for instant sandbox data.
- [x] **Testing**: Automated tests covering concurrency claim locks, backoffs, and dead letter transitions.

---

## Continuation Plan: Advanced Work

If you have additional time and want to make the submission even more competitive, consider implementing these advanced features:

### 1. Concurrency & Timeout Enforcement
- **Worker Job Timeout**:
  - Enforce timeouts on the worker runner. Currently, if a task hangs indefinitely, the worker thread will block.
  - *How to implement*: Wrap the payload execution in a future with a timeout (e.g. `executor.submit(execute_payload).result(timeout=job.timeout_seconds)`).
- **Distributed Locking via Redis**:
  - Add Redis-based distributed locking (using Redlock) to queues or specific job executions to guarantee single-concurrency across multiple distributed worker clusters.

### 2. Workflow Dependencies (DAGs)
- **Job Chain Execution**:
  - Allow a job to declare dependency on one or more parent jobs completing successfully before it runs.
  - *How to implement*:
    1. Create a `job_dependencies` table in the database mapping `parent_job_id` and `child_job_id`.
    2. Add a `BLOCKED` status to `JobStatus` enums.
    3. Modify `claim_next_job` to skip blocked jobs, and let `complete_job` check and unblock dependent child jobs once the parent job completes.

### 3. OpenTelemetry & Metrics Polish
- **Telemetry Integration**:
  - Integrate OpenTelemetry SDK in FastAPI, worker runner, and scheduler to record trace histories of background processes.
- **Prometheus Scraper**:
  - Expose `/metrics` endpoint on the FastAPI backend for Prometheus to scrape queue depths, processing times, and failure rates.

### 4. WebSocket Live Updates
- **Push Telemetry**:
  - Replace the current HTTP short-polling on the dashboard with a WebSocket route (`/api/v1/metrics/ws`) that streams queue and worker updates in real-time.

---

## Verification Checklist Before Submission

1. **Verify Backend Tests**:
   Ensure all automated tests pass:
   ```bash
   cd backend
   python -m pytest -q
   ```
2. **Build and Start Container Stack**:
   Verify that Docker Compose builds and starts all services (PostgreSQL, Redis, API, Worker, Scheduler, and React frontend):
   ```bash
   docker compose up --build
   ```
3. **Capture UI Screenshots**:
   Once the stack is running, log in using the demo account and capture screenshots of:
   - Dashboard Overview.
   - Queue configuration tables.
   - Jobs Explorer with the details drawer open.
   - Dead Letter Queue actions page.
   Save these screenshots in `docs/screenshots/` to present a clean package for evaluation.
