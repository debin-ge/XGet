from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.router import api_router
from .core.config import settings
from .core.logging import initialize_logging, logger
from .db.database import engine, Base
from .services.role_service import RoleService
import uvicorn

# Import models to ensure they are registered with SQLAlchemy
from .models import user, login_history, role, session

# 初始化日志系统
initialize_logging(
    log_level=settings.LOG_LEVEL,
    log_dir=settings.LOG_DIR
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="User Management Service for XGet Platform",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup():
    logger.info("User Service 启动中...")
    
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    
    # 初始化默认角色和权限
    from sqlalchemy.orm import Session
    from .services.user_service import UserService
    db = Session(engine)
    try:
        RoleService.initialize_default_roles(db)
        # 初始化admin用户
        UserService.initialize_admin_user(db)
    except Exception as e:
        logger.warning(f"Failed to initialize default data: {e}")
    finally:
        db.close()
    
    logger.info("User Service 启动完成")


@app.on_event("shutdown")
async def shutdown():
    logger.info("User Service 关闭中...")
    # 关闭数据库连接
    engine.dispose()
    logger.info("User Service 已关闭")


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "user-service",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "User Management Service",
        "version": "1.0.0",
        "docs": f"{settings.API_V1_STR}/docs"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 