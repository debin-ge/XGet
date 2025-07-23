from fastapi import APIRouter
from .storage import router as storage_router
from .metadata import router as metadata_router
from .lifecycle import router as lifecycle_router
from .stats import router as stats_router
from .backends import router as backends_router
from .policies import router as policies_router

api_router = APIRouter()

# 存储相关路由
api_router.include_router(
    storage_router, prefix="/storage", tags=["storage"]
)

# 元数据相关路由
api_router.include_router(
    metadata_router, prefix="/storage", tags=["metadata"]
)

# 生命周期相关路由
api_router.include_router(
    lifecycle_router, prefix="/storage/lifecycle", tags=["lifecycle"]
)

# 统计相关路由
api_router.include_router(
    stats_router, prefix="/storage/stats", tags=["stats"]
)

# 存储后端管理路由
api_router.include_router(
    backends_router, prefix="/backends", tags=["backends"]
)

# 保留策略管理路由
api_router.include_router(
    policies_router, prefix="/policies", tags=["policies"]
) 