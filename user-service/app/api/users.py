from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..db.database import get_db
from ..models.user import User
from ..schemas.user import (
    UserCreate, UserUpdate, User as UserSchema, UserWithRoles,
    UserPasswordUpdate, UserPreferences, UserStatus, UserLogin, UserLoginResponse,
    UserListResponse
)
from ..services.user_service import UserService
from ..core.security import get_current_user, get_current_active_user, check_permission
from ..core.logging import logger
from ..schemas.role import Role

router = APIRouter()


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """用户注册"""
    try:
        user = UserService.create_user(db, user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=UserLoginResponse)
async def login_user(
    user_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """用户登录"""
    try:
        # 认证用户
        user = UserService.authenticate_user(db, user_data.username, user_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # 创建会话
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent")
        
        session_data = UserService.create_user_session(
            db, user, client_ip, user_agent
        )
        
        return {
            "access_token": session_data["access_token"],
            "refresh_token": session_data["refresh_token"],
            "token_type": "bearer",
            "expires_in": 1800,  # 30 minutes
            "user": user
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """用户登出"""
    # 这里可以添加撤销令牌的逻辑
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserWithRoles)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户信息"""
    # 获取用户角色
    roles = UserService.get_user_roles(db, current_user.id)
    role_names = [role.name for role in roles]
    
    # Convert user to dict and handle None preferences
    user_dict = {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "phone": current_user.phone,
        "avatar_url": current_user.avatar_url,
        "timezone": current_user.timezone,
        "language": current_user.language,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "is_superuser": current_user.is_superuser,
        "last_login": current_user.last_login,
        "failed_login_attempts": current_user.failed_login_attempts,
        "locked_until": current_user.locked_until,
        "preferences": current_user.preferences or {},
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
        "roles": role_names
    }
    
    return UserWithRoles(**user_dict)


@router.put("/me", response_model=UserSchema)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    try:
        updated_user = UserService.update_user(db, current_user.id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/me/password")
async def update_current_user_password(
    password_data: UserPasswordUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新当前用户密码"""
    try:
        success = UserService.update_password(db, current_user.id, password_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return {"message": "Password updated successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/me/preferences")
async def update_current_user_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新当前用户偏好设置"""
    success = UserService.update_user_preferences(db, current_user.id, preferences.dict())
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "Preferences updated successfully"}


@router.get("/me/status", response_model=UserStatus)
async def get_current_user_status(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户状态"""
    return UserStatus(
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        is_locked=current_user.locked_until is not None and current_user.locked_until > datetime.utcnow(),
        locked_until=current_user.locked_until,
        failed_attempts=current_user.failed_login_attempts
    )


# 管理员接口
@router.get("/", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    current_user: User = Depends(check_permission("user:read")),
    db: Session = Depends(get_db)
):
    """获取用户列表（管理员）"""
    return UserService.get_users_paginated(db, page, size, is_active, is_verified)


@router.get("/{user_id}", response_model=UserWithRoles)
async def get_user(
    user_id: str,
    current_user: User = Depends(check_permission("user:read")),
    db: Session = Depends(get_db)
):
    """获取特定用户信息（管理员）"""
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 获取用户角色
    roles = UserService.get_user_roles(db, user_id)
    role_names = [role.name for role in roles]
    
    # Convert user to dict and handle None preferences
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "avatar_url": user.avatar_url,
        "timezone": user.timezone,
        "language": user.language,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "is_superuser": user.is_superuser,
        "last_login": user.last_login,
        "failed_login_attempts": user.failed_login_attempts,
        "locked_until": user.locked_until,
        "preferences": user.preferences or {},
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "roles": role_names
    }
    
    return UserWithRoles(**user_dict)


@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(check_permission("user:update")),
    db: Session = Depends(get_db)
):
    """更新用户信息（管理员）"""
    try:
        updated_user = UserService.update_user(db, user_id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(check_permission("user:delete")),
    db: Session = Depends(get_db)
):
    """删除用户（管理员）"""
    success = UserService.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/verify")
async def verify_user(
    user_id: str,
    current_user: User = Depends(check_permission("user:update")),
    db: Session = Depends(get_db)
):
    """验证用户邮箱（管理员）"""
    success = UserService.verify_user_email(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User verified successfully"}


@router.get("/{user_id}/roles", response_model=List[Role])
async def get_user_roles(
    user_id: str,
    current_user: User = Depends(check_permission("user:read")),
    db: Session = Depends(get_db)
):
    """获取用户角色列表"""
    # 检查用户是否存在
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 获取用户角色
    roles = UserService.get_user_roles(db, user_id)
    return roles 