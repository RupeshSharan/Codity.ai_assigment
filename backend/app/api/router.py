from fastapi import APIRouter

from app.api.routes import auth, jobs, metrics, organizations, queues, workers

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(queues.router, prefix="/queues", tags=["queues"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(workers.router, prefix="/workers", tags=["workers"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])

