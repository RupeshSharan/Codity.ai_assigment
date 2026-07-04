# PulseQueue

PulseQueue is a production-inspired distributed job scheduling platform for asynchronous background work. It is built around project isolation, configurable queues, atomic job claiming, worker heartbeats, retries, execution history, and a dashboard-oriented operations experience.

## Assignment Fit

The original assignment emphasizes engineering quality over feature count. This implementation therefore focuses on the highest-scoring areas first:

- Relational schema for users, organizations, projects, queues, jobs, executions, retry policies, workers, heartbeats, logs, and Dead Letter Queue entries.
- FastAPI REST APIs with validation, authentication, structured errors, pagination-ready job listing, and operational routes.
- Atomic claim service that prevents duplicate execution and respects paused queues plus queue concurrency limits.
- Worker runner, scheduler tick, heartbeat recovery, retries, and DLQ transitions.
- React dashboard scaffold for overview metrics, queues, jobs, workers, and failed-job operations.
- Docker Compose for PostgreSQL, Redis, API, scheduler, worker, and frontend.
- Pytest coverage for critical reliability behavior.

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, TypeScript, Tailwind CSS, Recharts |
| Backend | FastAPI |
| Database | PostgreSQL in Docker, SQLite fallback for local dev/tests |
| ORM/Migrations | SQLAlchemy, Alembic |
| Cache | Redis |
| Auth | Signed JWT, PBKDF2 password hashing |
| Tests | Pytest |
| Runtime | Docker Compose |

## Quick Start

Copy the environment template:

```bash
cp .env.example .env
```

Run the full stack:

```bash
docker compose up --build
```

Open:

- API health: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`
- Dashboard: `http://localhost:5173`

## Local Backend Development

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Run tests:

```bash
cd backend
python -m pytest -q
```

## Worker and Scheduler

Run a scheduler loop:

```bash
cd backend
python -m app.scheduler.service
```

Run a worker:

```bash
cd backend
set WORKER_ID=worker-local-1
set WORKER_CONCURRENCY=4
python -m app.workers.runner
```

## Key Documents

- [Assignment Comparison](docs/ASSIGNMENT_COMPARISON.md)
- [Architecture](docs/ARCHITECTURE.md)
- [ER Diagram](docs/ER_DIAGRAM.md)
- [API Documentation](docs/API.md)
- [Database Design](docs/DATABASE_DESIGN.md)
- [Design Decisions](docs/DESIGN_DECISIONS.md)
- [Next Steps](docs/NEXT_STEPS.md)

