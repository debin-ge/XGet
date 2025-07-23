from fastapi import Request, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from ..core.config import settings
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

# 不需要认证的路径列表
PUBLIC_PATHS = [
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/docs",
    "/api/v1/redoc",
    "/api/v1/openapi.json",
    "/health",
    "/metrics",
]

# OAuth2密码流认证
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


def is_public_path(path: str) -> bool:
    """
    检查路径是否是公开的（不需要认证）
    """
    for public_path in PUBLIC_PATHS:
        if path.startswith(public_path):
            return True
    return False


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
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # 解码JWT令牌
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # 将用户信息添加到请求状态
        request.state.user = payload
        
        return True
    except JWTError as e:
        logger.error(f"JWT验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"认证过程中发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error",
        ) 