from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import logging
import time
from .core.config import settings
import uvicorn

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # 处理请求
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # 记录请求信息
        logger.info(
            f"{request.method} {request.url.path} "
            f"- Status: {response.status_code} "
            f"- Process Time: {process_time:.3f}s"
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"{request.method} {request.url.path} "
            f"- Error: {str(e)} "
            f"- Process Time: {process_time:.3f}s"
        )
        
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# 健康检查端点
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}

# 测试端点
@app.get("/", tags=["root"])
async def root():
    return {"message": "XGet API Gateway"}

# API版本端点
@app.get("/api/v1", tags=["api"])
async def api_root():
    return {"version": "1.0", "status": "ok"}

# 账号服务代理端点
@app.api_route("/api/v1/accounts/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def account_proxy(request: Request, path: str):
    return await proxy_request(request, "account-service", f"/api/v1/{path}")

# 代理服务代理端点
@app.api_route("/api/v1/proxies/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_proxy(request: Request, path: str):
    return await proxy_request(request, "proxy-service", f"/api/v1/{path}")

# 数据采集服务代理端点
@app.api_route("/api/v1/scrapers/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def scraper_proxy(request: Request, path: str):
    return await proxy_request(request, "scraper-service", f"/api/v1/{path}")

# 代理请求到其他服务
async def proxy_request(request: Request, service: str, path: str):
    service_url = settings.SERVICES.get(service)
    if not service_url:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")
    
    target_url = f"{service_url}{path}"
    
    # 获取请求方法和头信息
    method = request.method
    headers = dict(request.headers)
    headers.pop("host", None)
    
    # 获取查询参数
    params = dict(request.query_params)
    
    # 获取请求体
    body = None
    if method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
    
    # 创建httpx客户端
    async with httpx.AsyncClient() as client:
        try:
            # 转发请求
            response = await client.request(
                method=method,
                url=target_url,
                headers=headers,
                params=params,
                content=body,
                timeout=30.0
            )
            
            # 返回响应
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except httpx.RequestError as e:
            logger.error(f"Error forwarding request to {service}: {str(e)}")
            raise HTTPException(status_code=503, detail=f"Service '{service}' is unavailable")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    ) 