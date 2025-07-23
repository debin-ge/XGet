from fastapi import APIRouter
from .processing_tasks import router as processing_tasks_router
from .processing_rules import router as processing_rules_router
from .processing_results import router as processing_results_router

api_router = APIRouter()

api_router.include_router(
    processing_tasks_router, prefix="/processing-tasks", tags=["processing-tasks"]
)
api_router.include_router(
    processing_rules_router, prefix="/processing-rules", tags=["processing-rules"]
)
api_router.include_router(
    processing_results_router, prefix="/processing-results", tags=["processing-results"]
) 