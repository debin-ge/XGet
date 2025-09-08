from fastapi import APIRouter
from .proxies import router as proxies_router
from .analytics import router as analytics_router

api_router = APIRouter()
api_router.include_router(proxies_router, prefix="/proxies", tags=["proxies"])
api_router.include_router(analytics_router, prefix="/analytics/proxies", tags=["analytics"])
