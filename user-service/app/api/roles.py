from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..db.database import get_db
from ..models.user import User
from ..schemas.role import (
    RoleCreate, RoleUpdate, Role as RoleSchema, Permission as PermissionSchema,
    PermissionCreate, UserRoleCreate, RoleAssignment, RoleRemoval
)
from ..services.role_service import RoleService
from ..services.user_service import UserService
from ..core.security import check_permission
from ..core.logging import logger

router = APIRouter()


# 权限管理 (放在角色管理之前，避免路由冲突)
@router.post("/permissions", response_model=PermissionSchema, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionCreate,
    current_user: User = Depends(check_permission("role:create")),
    db: Session = Depends(get_db)
):
    """创建新权限"""
    try:
        permission = RoleService.create_permission(db, permission_data)
        return permission
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/permissions", response_model=List[PermissionSchema])
async def get_permissions(
    skip: int = 0,
    limit: int = 100,
    resource: Optional[str] = None,
    action: Optional[str] = None,
    current_user: User = Depends(check_permission("role:read")),
    db: Session = Depends(get_db)
):
    """获取权限列表"""
    permissions = RoleService.get_permissions(db, skip, limit, resource, action)
    return permissions


@router.get("/permissions/{permission_id}", response_model=PermissionSchema)
async def get_permission(
    permission_id: str,
    current_user: User = Depends(check_permission("role:read")),
    db: Session = Depends(get_db)
):
    """获取特定权限"""
    permission = RoleService.get_permission_by_id(db, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    return permission


# 用户角色管理 (也需要放在角色管理之前)
@router.post("/assign", status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    assignment: RoleAssignment,
    current_user: User = Depends(check_permission("user:update")),
    db: Session = Depends(get_db)
):
    """为用户分配角色"""
    success = UserService.assign_role_to_user(
        db, 
        assignment.user_id, 
        assignment.role_id, 
        current_user.id,
        assignment.expires_at
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to assign role to user"
        )
    
    return {"message": "Role assigned successfully"}


@router.delete("/remove")
async def remove_role_from_user(
    removal: RoleRemoval,
    current_user: User = Depends(check_permission("user:update")),
    db: Session = Depends(get_db)
):
    """移除用户角色"""
    success = UserService.remove_role_from_user(db, removal.user_id, removal.role_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove role from user"
        )
    
    return {"message": "Role removed successfully"}


@router.get("/users/{user_id}/roles", response_model=List[RoleSchema])
async def get_user_roles(
    user_id: str,
    current_user: User = Depends(check_permission("user:read")),
    db: Session = Depends(get_db)
):
    """获取用户角色"""
    roles = UserService.get_user_roles(db, user_id)
    return roles


@router.get("/users/{user_id}/permissions", response_model=List[PermissionSchema])
async def get_user_permissions(
    user_id: str,
    current_user: User = Depends(check_permission("user:read")),
    db: Session = Depends(get_db)
):
    """获取用户权限"""
    permissions = RoleService.get_user_permissions(db, user_id)
    return permissions


# 初始化默认角色
@router.post("/initialize-defaults")
async def initialize_default_roles(
    current_user: User = Depends(check_permission("role:create")),
    db: Session = Depends(get_db)
):
    """初始化默认角色和权限"""
    success = RoleService.initialize_default_roles(db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize default roles"
        )
    
    return {"message": "Default roles initialized successfully"}


# 角色管理 (放在最后，避免与具体路由冲突)
@router.post("/", response_model=RoleSchema, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(check_permission("role:create")),
    db: Session = Depends(get_db)
):
    """创建新角色"""
    try:
        role = RoleService.create_role(db, role_data)
        return role
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[RoleSchema])
async def get_roles(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    current_user: User = Depends(check_permission("role:read")),
    db: Session = Depends(get_db)
):
    """获取角色列表"""
    roles = RoleService.get_roles(db, skip, limit, is_active)
    return roles


@router.get("/{role_id}", response_model=RoleSchema)
async def get_role(
    role_id: str,
    current_user: User = Depends(check_permission("role:read")),
    db: Session = Depends(get_db)
):
    """获取特定角色"""
    role = RoleService.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return role


@router.put("/{role_id}", response_model=RoleSchema)
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    current_user: User = Depends(check_permission("role:update")),
    db: Session = Depends(get_db)
):
    """更新角色"""
    try:
        role = RoleService.update_role(db, role_id, role_data)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        return role
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    current_user: User = Depends(check_permission("role:delete")),
    db: Session = Depends(get_db)
):
    """删除角色"""
    try:
        success = RoleService.delete_role(db, role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        return {"message": "Role deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 