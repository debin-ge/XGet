from fastapi import APIRouter
from .tasks import router as tasks_router
from .task_executions import router as task_executions_router
from .analytics import router as analytics_router

api_router = APIRouter()
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(task_executions_router, prefix="/task-executions", tags=["task-executions"])
api_router.include_router(analytics_router, prefix="/tasks/analytics", tags=["analytics"])
