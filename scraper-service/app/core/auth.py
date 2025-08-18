from typing import Optional, List
from fastapi import Request, HTTPException, Depends, status


def get_current_user_id(request: Request) -> str:
    """
    从请求头中获取当前用户ID
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        str: 用户ID
        
    Raises:
        HTTPException: 如果没有找到用户ID
    """
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in request headers"
        )
    return user_id


def get_current_username(request: Request) -> Optional[str]:
    """
    从请求头中获取当前用户名
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        Optional[str]: 用户名，如果不存在则返回None
    """
    return request.headers.get("X-Username")


def get_current_user_roles(request: Request) -> List[str]:
    """
    从请求头中获取当前用户角色
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        List[str]: 用户角色列表
    """
    roles_header = request.headers.get("X-User-Roles", "")
    if not roles_header:
        return []
    return [role.strip() for role in roles_header.split(",") if role.strip()]


def is_current_user_superuser(request: Request) -> bool:
    """
    检查当前用户是否为超级用户
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        bool: 是否为超级用户
    """
    is_superuser = request.headers.get("X-Is-Superuser", "false")
    return is_superuser.lower() == "true"


def require_admin_permission(request: Request) -> bool:
    """
    检查当前用户是否有管理员权限
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        bool: 是否有管理员权限
        
    Raises:
        HTTPException: 如果没有管理员权限
    """
    user_roles = get_current_user_roles(request)
    is_superuser = is_current_user_superuser(request)
    
    if "admin" not in user_roles and not is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: Admin access required"
        )
    
    return True 