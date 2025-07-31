from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.router import api_router
from .core.config import settings
from .core.logging import initialize_logging, logger
from .db.database import engine, Base
import uvicorn

# 初始化日志系统
initialize_logging(
    log_level=settings.LOG_LEVEL,
    log_dir=settings.LOG_DIR
)

app = FastAPI(
    title=settings.PROJECT_NAME,
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

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup():
    logger.info("服务启动中...")
    # 创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("服务启动完成")

@app.on_event("shutdown")
async def shutdown():
    logger.info("服务关闭中...")
    # 关闭数据库连接
    await engine.dispose()
    logger.info("服务已关闭")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
