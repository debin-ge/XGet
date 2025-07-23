from fastapi import APIRouter
from .routes import account, proxy, scraper

api_router = APIRouter()

# 账号管理服务路由
api_router.include_router(account.router, prefix="/accounts", tags=["accounts"])

# 代理管理服务路由
api_router.include_router(proxy.router, prefix="/proxies", tags=["proxies"])

# 数据采集服务路由
api_router.include_router(scraper.router, prefix="/scrapers", tags=["scrapers"]) 