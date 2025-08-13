from fastapi import APIRouter
from .users import router as users_router
from .roles import router as roles_router
from .auth import router as auth_router

api_router = APIRouter()

# 用户相关路由
api_router.include_router(
    users_router,
    prefix="/users",
    tags=["users"]
)

# 角色和权限相关路由
api_router.include_router(
    roles_router,
    prefix="/roles",
    tags=["roles"]
)

# 认证相关路由
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"]
) 