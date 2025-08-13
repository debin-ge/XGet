from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
from ...middlewares.proxy import service_router
from ...middlewares.auth import verify_token
from fastapi.responses import JSONResponse

router = APIRouter()

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def scraper_route(
    request: Request,
    path: str,
    auth_required: bool = Depends(verify_token)
):
    """
    数据采集服务路由转发
    
    所有发送到 /api/v1/tasks/* 和 /api/v1/scrapers/* 的请求都会被转发到数据采集服务
    处理采集任务的创建、执行、监控和结果获取等功能
    """
    
    response = await service_router.forward_request(
        request=request,
        service_name="scraper-service",
        path=request.url.path,
    )
    
    return JSONResponse(
        content=response["data"],
        status_code=response["status_code"],
        headers={k: v for k, v in response["headers"].items() if k.lower() not in ["content-length", "transfer-encoding"]}
    ) 