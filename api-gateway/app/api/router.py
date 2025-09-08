from fastapi import APIRouter
from .routes import account, proxy, scraper, user, analytics

api_router = APIRouter()

# 用户管理服务路由
api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(user.router, prefix="/roles", tags=["roles"])
api_router.include_router(user.router, prefix="/auth", tags=["auth"])

# 账号管理服务路由
api_router.include_router(account.router, prefix="/accounts", tags=["accounts"])

# 代理管理服务路由
api_router.include_router(proxy.router, prefix="/proxies", tags=["proxies"])

# 数据采集服务路由
api_router.include_router(scraper.router, prefix="/tasks", tags=["scraper"])

# 数据分析服务路由
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

# 保持与现有API的兼容性，添加别名路由
api_router.include_router(scraper.router, prefix="/task-executions", tags=["task-executions"]) 