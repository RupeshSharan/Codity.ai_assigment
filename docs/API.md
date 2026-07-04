# API Documentation

FastAPI generates interactive OpenAPI docs at `/docs`.

## Authentication

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/auth/register` | Create a user and first organization |
| `POST` | `/api/v1/auth/login` | Exchange email/password for bearer token |
| `GET` | `/api/v1/auth/me` | Read current user |

## Organizations and Projects

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/organizations` | List organizations visible to the user |
| `POST` | `/api/v1/organizations` | Create organization |
| `POST` | `/api/v1/organizations/{organization_id}/projects` | Create project |
| `GET` | `/api/v1/organizations/{organization_id}/projects` | List projects |

## Queues and Retry Policies

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/queues/retry-policies/{project_id}` | Create retry policy |
| `GET` | `/api/v1/queues/retry-policies/{project_id}` | List retry policies |
| `POST` | `/api/v1/queues` | Create queue |
| `GET` | `/api/v1/queues?project_id=...` | List queues |
| `PATCH` | `/api/v1/queues/{queue_id}` | Update queue config |
| `POST` | `/api/v1/queues/{queue_id}/pause` | Pause queue |
| `POST` | `/api/v1/queues/{queue_id}/resume` | Resume queue |
| `GET` | `/api/v1/queues/{queue_id}/stats` | Queue statistics |

## Jobs

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/jobs` | Create immediate, delayed, scheduled, recurring, or tagged job |
| `POST` | `/api/v1/jobs/batch` | Submit batch jobs |
| `GET` | `/api/v1/jobs` | Filter jobs by project, queue, worker, status, tag |
| `GET` | `/api/v1/jobs/{job_id}` | Job detail with executions and logs |
| `GET` | `/api/v1/jobs/dead-letter/list?project_id=...` | List DLQ jobs |
| `POST` | `/api/v1/jobs/{job_id}/retry` | Requeue DLQ job |

## Workers

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/workers/register` | Register worker |
| `GET` | `/api/v1/workers` | List workers |
| `POST` | `/api/v1/workers/{worker_id}/heartbeat` | Record heartbeat |
| `POST` | `/api/v1/workers/{worker_id}/claim` | Atomically claim next job |
| `POST` | `/api/v1/workers/{worker_id}/jobs/{job_id}/start` | Mark job running |
| `POST` | `/api/v1/workers/{worker_id}/jobs/{job_id}/complete` | Complete job |
| `POST` | `/api/v1/workers/{worker_id}/jobs/{job_id}/fail` | Fail job and retry/DLQ |

## Metrics

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/metrics/overview` | Dashboard overview metrics |

