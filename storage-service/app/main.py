from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import time
from .core.config import settings
from .db.database import init_db
from .api.router import api_router
from .tasks.kafka_consumer import start_kafka_consumer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# 配置CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    return response

# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 启动事件
@app.on_event("startup")
async def startup_event():
    logger.info("正在启动数据存储服务...")
    await init_db()
    # 启动Kafka消费者
    await start_kafka_consumer()
    logger.info("数据存储服务启动完成")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("正在关闭数据存储服务...")
    # 关闭Elasticsearch连接
    from .db.database import es_client
    if es_client:
        await es_client.close()

# 健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}

# 根路径重定向到文档
@app.get("/")
async def root():
    return {"message": "欢迎使用XGet数据存储服务", "docs_url": f"{settings.API_V1_STR}/docs"} 