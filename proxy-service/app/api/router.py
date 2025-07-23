from fastapi import APIRouter
from .proxies import router as proxies_router

api_router = APIRouter()
api_router.include_router(proxies_router, prefix="/proxies", tags=["proxies"])
