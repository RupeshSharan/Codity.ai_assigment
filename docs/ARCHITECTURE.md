# Architecture

PulseQueue separates control-plane APIs from background execution. Users and operators interact through the React dashboard and REST API. Workers are independent processes that poll for work, claim jobs atomically, execute payload handlers, and report lifecycle transitions. A scheduler service handles delayed jobs and stale-worker recovery.

```mermaid
flowchart TB
    UI["React + TypeScript Dashboard"] --> API["FastAPI REST API"]
    API --> Auth["JWT Auth + Project Permissions"]
    API --> QueueMgr["Queue Manager"]
    API --> JobMgr["Job Lifecycle Service"]
    API --> Metrics["Metrics Service"]
    Scheduler["Scheduler Service"] --> DB[(PostgreSQL)]
    Scheduler --> Redis[(Redis)]
    WorkerA["Worker Process A"] --> JobMgr
    WorkerB["Worker Process B"] --> JobMgr
    JobMgr --> DB
    QueueMgr --> DB
    Metrics --> DB
    Auth --> DB
    API --> DB
```

## Runtime Services

- `api`: FastAPI app exposing `/api/v1`.
- `scheduler`: Promotes due scheduled jobs, marks stale workers offline, and requeues stale claimed/running jobs.
- `worker`: Registers itself, sends heartbeats, claims jobs, executes jobs concurrently, and reports success/failure.
- `postgres`: Primary relational store.
- `redis`: Reserved for cache/rate limiting/distributed locking extensions.
- `frontend`: React dashboard.

## Reliability Flow

```mermaid
sequenceDiagram
    participant Worker
    participant API
    participant DB
    Worker->>API: register
    Worker->>API: heartbeat
    Worker->>API: claim next job
    API->>DB: atomic status update queued -> claimed
    DB-->>API: claimed job or none
    Worker->>API: start job
    API->>DB: create execution, claimed -> running
    alt success
        Worker->>API: complete job
        API->>DB: running -> completed
    else failure with attempts remaining
        Worker->>API: fail job
        API->>DB: running -> scheduled retry
    else permanent failure
        Worker->>API: fail job
        API->>DB: running -> dead_letter + DLQ entry
    end
```

## Atomic Claiming

The `claim_next_job` service scans eligible jobs by priority and scheduled time, filters out paused queues, checks queue concurrency, and performs a guarded status update. PostgreSQL can use row locks with `SKIP LOCKED`; SQLite tests use a guarded update to prove only one caller transitions a queued job to claimed.

