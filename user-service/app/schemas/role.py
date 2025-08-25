from pydantic import BaseModel
from typing import Optional, List, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """通用分页响应模式"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    
    @classmethod
    def create(cls, items: List[T], total: int, page: int, size: int):
        """创建分页响应"""
        pages = (total + size - 1) // size if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )


class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None
    resource: str
    action: str


class PermissionCreate(PermissionBase):
    pass


class Permission(PermissionBase):
    id: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    permission_ids: List[str] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permission_ids: Optional[List[str]] = None


class Role(RoleBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    permissions: List[Permission] = []
    
    class Config:
        from_attributes = True


class RoleListResponse(PaginatedResponse[Role]):
    """角色列表分页响应"""
    pass


class PermissionListResponse(PaginatedResponse[Permission]):
    """权限列表分页响应"""
    pass


class UserRoleBase(BaseModel):
    role_id: str
    expires_at: Optional[datetime] = None


class UserRoleCreate(UserRoleBase):
    pass


class UserRole(UserRoleBase):
    id: str
    user_id: str
    assigned_by: Optional[str] = None
    assigned_at: datetime
    is_active: bool
    role: Role
    
    class Config:
        from_attributes = True


class RoleAssignment(BaseModel):
    user_id: str
    role_id: str
    expires_at: Optional[datetime] = None


class RoleRemoval(BaseModel):
    user_id: str
    role_id: str 