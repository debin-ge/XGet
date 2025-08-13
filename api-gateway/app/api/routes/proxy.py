from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
from ...middlewares.proxy import service_router
from ...middlewares.auth import verify_token
from fastapi.responses import JSONResponse

router = APIRouter()

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_route(
    request: Request,
    path: str,
    auth_required: bool = Depends(verify_token)
):
    """
    代理管理服务路由转发
    
    所有发送到 /api/v1/proxies/* 的请求都会被转发到代理管理服务
    处理代理池管理、代理检查、代理轮换等功能
    """
    response = await service_router.forward_request(
        request=request,
        service_name="proxy-service",
        path=request.url.path,
    )
    
    return JSONResponse(
        content=response["data"],
        status_code=response["status_code"],
        headers={k: v for k, v in response["headers"].items() if k.lower() not in ["content-length", "transfer-encoding"]}
    ) 