from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .core.logging import initialize_logging, logger
import asyncio
import time
from contextlib import asynccontextmanager

from .core.config import settings
from .api.router import api_router
from .middlewares.rate_limit import rate_limiter, rate_limit_middleware
from .middlewares.monitoring import monitoring_middleware, get_metrics_response
from .middlewares.security import security_headers_middleware, request_id_middleware
from .middlewares.proxy import service_router
from .services.health_checker import health_checker


# 初始化日志系统
initialize_logging(
    log_level=settings.LOG_LEVEL,
    log_dir=settings.LOG_DIR
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时的初始化
    logger.info("正在启动 XGet API Gateway...")
    
    # 初始化Redis连接（用于限流）
    if settings.RATE_LIMIT_ENABLED:
        await rate_limiter.init_redis()
    
    # 启动健康检查器
    await health_checker.start()
    
    logger.info("XGet API Gateway 启动完成")
    
    yield
    
    # 关闭时的清理
    logger.info("正在关闭 XGet API Gateway...")
    
    # 停止健康检查器
    await health_checker.stop()
    
    # 关闭Redis连接
    if settings.RATE_LIMIT_ENABLED:
        await rate_limiter.close_redis()
    
    # 关闭HTTP客户端
    await service_router.close()
    
    logger.info("XGet API Gateway 已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="XGet 数据抓取平台的 API 网关，提供统一的入口和认证、限流、监控等功能",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加安全头中间件
if settings.SECURITY_HEADERS_ENABLED:
    app.middleware("http")(security_headers_middleware)

# 添加请求ID中间件
app.middleware("http")(request_id_middleware)

# 添加监控中间件
if settings.METRICS_ENABLED:
    app.middleware("http")(monitoring_middleware)

# 添加限流中间件
if settings.RATE_LIMIT_ENABLED:
    app.middleware("http")(rate_limit_middleware)

# 添加API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 健康检查端点
@app.get("/health", tags=["健康检查"])
async def health_check():
    """
    健康检查端点
    
    检查API网关和后端服务的健康状态
    """
    health_status = {
        "status": "healthy",
        "timestamp": int(asyncio.get_event_loop().time()),
        "services": {}
    }
    
    # 使用健康检查器获取服务状态
    if settings.HEALTH_CHECK_ENABLED:
        health_summary = health_checker.get_health_summary()
        health_status.update(health_summary)
    else:
        # 如果健康检查被禁用，进行简单的即时检查
        for service_name, service_url in settings.SERVICES.items():
            try:
                # 简单的健康检查请求
                import httpx
                async with httpx.AsyncClient(timeout=settings.HEALTH_CHECK_TIMEOUT_SECONDS) as client:
                    response = await client.get(f"{service_url}/health")
                    if response.status_code == 200:
                        health_status["services"][service_name] = "healthy"
                    else:
                        health_status["services"][service_name] = "unhealthy"
            except Exception:
                health_status["services"][service_name] = "unreachable"
        
        # 检查是否有服务不健康
        unhealthy_services = [k for k, v in health_status["services"].items() if v != "healthy"]
        if unhealthy_services:
            health_status["status"] = "degraded"
            health_status["unhealthy_services"] = unhealthy_services
    
    return health_status


# 指标端点（由监控中间件处理）
@app.get("/metrics", tags=["监控"])
async def metrics():
    """Prometheus 指标端点"""
    return get_metrics_response()


# 根端点
@app.get("/", tags=["信息"])
async def root():
    """
    API 根端点
    
    返回API网关的基本信息
    """
    return {
        "message": "XGet API Gateway",
        "version": "1.0.0",
        "description": "XGet 数据抓取平台的统一API入口",
        "docs_url": f"{settings.API_V1_STR}/docs",
        "health_url": "/health",
        "metrics_url": "/metrics" if settings.METRICS_ENABLED else None
    }


# API版本信息端点
@app.get(f"{settings.API_V1_STR}", tags=["信息"])
async def api_info():
    """
    API 版本信息
    """
    return {
        "version": "v1",
        "status": "active",
        "services": {
            "users": f"{settings.API_V1_STR}/users",
            "accounts": f"{settings.API_V1_STR}/accounts",
            "proxies": f"{settings.API_V1_STR}/proxies",
            "tasks": f"{settings.API_V1_STR}/tasks",
            "scrapers": f"{settings.API_V1_STR}/scrapers"  # 兼容性别名
        }
    }


# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    error_response = {
        "error": exc.detail,
        "status_code": exc.status_code,
        "request_id": request_id,
        "path": str(request.url.path),
        "timestamp": time.time()
    }
    
    # 根据错误状态码确定日志级别
    if exc.status_code == 503:
        # 服务不可用 - 可能是暂时的，使用WARNING级别
        logger.warning(f"Service unavailable on {request.url.path}: {exc.detail} (request_id: {request_id})")
        
        # 为503错误添加重试信息
        if "unavailable after" in str(exc.detail):
            error_response["retry_after"] = 60  # 建议60秒后重试
            error_response["error_type"] = "service_unavailable"
            
    elif exc.status_code >= 500:
        # 服务器错误
        logger.error(f"HTTP {exc.status_code} error on {request.url.path}: {exc.detail} (request_id: {request_id})")
    elif exc.status_code == 429:
        # 限流错误
        logger.warning(f"Rate limit exceeded on {request.url.path} (request_id: {request_id})")
    elif exc.status_code >= 400:
        # 客户端错误
        logger.info(f"HTTP {exc.status_code} error on {request.url.path}: {exc.detail} (request_id: {request_id})")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=exc.headers
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    error_response = {
        "error": "Internal server error",
        "status_code": 500,
        "request_id": request_id,
        "path": str(request.url.path)
    }
    
    # 记录详细错误信息
    logger.error(f"Unhandled exception on {request.url.path}: {str(exc)} (request_id: {request_id})", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=error_response
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 