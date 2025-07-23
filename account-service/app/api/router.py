from fastapi import APIRouter
from .accounts import router as accounts_router
from .login_history import router as login_history_router

api_router = APIRouter()
api_router.include_router(accounts_router, prefix="/accounts", tags=["accounts"])
api_router.include_router(login_history_router, prefix="/login-history", tags=["login-history"])
