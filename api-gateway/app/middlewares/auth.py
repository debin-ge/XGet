from fastapi import Request, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from ..core.config import settings
from typing import Dict, Any, Optional, List
import logging
import httpx

logger = logging.getLogger(__name__)

# 不需要认证的路径列表
PUBLIC_PATHS = [
    # 认证相关路径
    "/api/v1/auth/login",
    "/api/v1/auth/register", 
    "/api/v1/auth/refresh",
    "/api/v1/users/login",
    "/api/v1/users/register",
    # 文档和健康检查
    "/api/v1/docs",
    "/api/v1/redoc", 
    "/api/v1/openapi.json",
    "/health",
    "/metrics",
    "/",
    # 根路径API信息
    "/api/v1",
]

# 需要管理员权限的路径
ADMIN_REQUIRED_PATHS = [
    "/api/v1/users",  # 用户管理
    "/api/v1/roles",  # 角色管理
    "/api/v1/accounts/create",  # 创建账户
    "/api/v1/accounts/import",  # 导入账户
    "/api/v1/proxies/import",  # 导入代理
]

# OAuth2密码流认证
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def is_public_path(path: str) -> bool:
    """
    检查路径是否是公开的（不需要认证）
    """
    if path in PUBLIC_PATHS:
        return True

    return False


def requires_admin_permission(path: str, method: str) -> bool:
    """
    检查路径是否需要管理员权限
    """
    for admin_path in ADMIN_REQUIRED_PATHS:
        if path.startswith(admin_path):
            # POST, PUT, DELETE 通常需要更高权限
            if method.upper() in ["POST", "PUT", "DELETE"]:
                return True
    return False


async def verify_user_with_service(token: str) -> Optional[Dict[str, Any]]:
    """
    通过用户服务验证用户令牌
    """
    try:
        user_service_url = settings.SERVICES.get("user-service")
        if not user_service_url:
            logger.error("User service URL not configured")
            return None
            
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{user_service_url}/api/v1/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"User verification failed with status {response.status_code}")
                return None
                
    except Exception as e:
        logger.error(f"Error verifying user with service: {str(e)}")
        return None


async def verify_token(request: Request, token: str = Depends(oauth2_scheme)) -> bool:
    """
    验证JWT令牌
    
    Args:
        request: 请求对象
        token: JWT令牌
        
    Returns:
        bool: 认证是否成功
        
    Raises:
        HTTPException: 如果认证失败
    """
    # 检查是否是公开路径
    if is_public_path(request.url.path):
        return True
    
    # 检查是否提供了令牌
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # 首先尝试本地验证JWT令牌
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # 检查令牌类型
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 通过用户服务获取完整的用户信息
        user_info = await verify_user_with_service(token)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User verification failed",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 检查用户状态
        if not user_info.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 检查管理员权限
        if requires_admin_permission(request.url.path, request.method):
            user_roles = user_info.get("roles", [])
            if "admin" not in user_roles and not user_info.get("is_superuser", False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions",
                )
        
        # 将用户信息添加到请求状态
        request.state.user = user_info
        request.state.token_payload = payload
        
        return True
        
    except JWTError as e:
        logger.error(f"JWT验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        logger.error(f"认证过程中发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error",
        )


def get_current_user(request: Request) -> Dict[str, Any]:
    """
    从请求状态中获取当前用户信息
    """
    if hasattr(request.state, "user"):
        return request.state.user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated"
    ) 