from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.router import api_router
from .core.config import settings
import asyncio
from .db.database import engine, Base
from .tasks.worker import task_worker

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
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
    # 创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 启动任务工作器
    asyncio.create_task(task_worker.start())

@app.on_event("shutdown")
async def shutdown():
    # 停止任务工作器
    await task_worker.stop()
    
    # 关闭数据库连接
    await engine.dispose()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 添加一个临时的根路径端点
@app.get("/")
async def root():
    return {"message": "XGet Scraper Service - Temporary Mode"}

# 添加一个临时的API版本端点
@app.get(f"{settings.API_V1_STR}")
async def api_root():
    return {
        "version": "1.0",
        "status": "maintenance",
        "message": "服务正在维护中，MongoDB依赖问题正在解决"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
