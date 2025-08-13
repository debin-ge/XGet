from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
from ...middlewares.proxy import service_router
from ...middlewares.auth import verify_token, is_public_path
from fastapi.responses import JSONResponse
from ...core.logging import logger

router = APIRouter()

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def user_route(
    request: Request,
    path: str,
    auth_required: bool = Depends(verify_token)
):
    """
    用户管理服务路由转发
    
    所有发送到 user-service 的请求都会被转发到用户管理服务
    处理用户注册、登录、认证、角色管理等功能
    """
    # 对于公开路径（如登录、注册），不需要包含认证令牌
    include_token = not is_public_path(request.url.path)
    

    response = await service_router.forward_request(
        request=request,
        service_name="user-service",
        path=request.url.path,
        include_token=include_token
    )
    
    return JSONResponse(
        content=response["data"],
        status_code=response["status_code"],
        headers={k: v for k, v in response["headers"].items() if k.lower() not in ["content-length", "transfer-encoding"]}
    ) 