from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


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