from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import init_db
from app.core.data_connector import init_data_connections, data_connector
from app.core.cache import init_redis, redis_cache
from .core.logging import initialize_logging, logger


# 初始化日志系统
initialize_logging(
    log_level=settings.LOG_LEVEL,
    log_dir=settings.LOG_DIR
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize all connections
    await init_db()
    await init_data_connections()
    await init_redis()
    yield
    # Shutdown: Close all connections
    await data_connector.close_connections()
    await redis_cache.close()


def create_application() -> FastAPI:
    application = FastAPI(
        title="XGet Analytics Service",
        description="Analytics and statistics service for XGet platform",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Set all CORS enabled origins
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    application.include_router(api_router, prefix=settings.API_V1_STR)

    # Add health check endpoint
    @application.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "analytics"}

    # Add root endpoint
    @application.get("/")
    async def root():
        return {"message": "XGet Analytics Service"}

    return application


app = create_application()