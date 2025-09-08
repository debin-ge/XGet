from fastapi import APIRouter

from app.api.v1.endpoints import accounts, proxies, tasks, metrics, results, jobs, activities

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(accounts.router, prefix="/analytics/accounts", tags=["Account Analytics"])
api_router.include_router(proxies.router, prefix="/analytics/proxies", tags=["Proxy Analytics"])
api_router.include_router(tasks.router, prefix="/analytics/tasks", tags=["Task Analytics"])
api_router.include_router(results.router, prefix="/analytics/results", tags=["Result Analytics"])
api_router.include_router(metrics.router, prefix="/analytics/metrics", tags=["Metrics Management"])
api_router.include_router(jobs.router, prefix="/analytics/jobs", tags=["Jobs Management"])
api_router.include_router(activities.router, prefix="/analytics/activities", tags=["Activities"])