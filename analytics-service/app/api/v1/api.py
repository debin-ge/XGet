from fastapi import APIRouter

from app.api.v1.endpoints import accounts, proxies, tasks, activities

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(accounts.router, prefix="/analytics/accounts", tags=["Account Analytics"])
api_router.include_router(proxies.router, prefix="/analytics/proxies", tags=["Proxy Analytics"])
api_router.include_router(tasks.router, prefix="/analytics/tasks", tags=["Task Analytics"])
api_router.include_router(activities.router, prefix="/analytics/activities", tags=["Activities"])