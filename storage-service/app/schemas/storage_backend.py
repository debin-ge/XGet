from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class StorageBackendBase(BaseModel):
    """存储后端基础模型"""
    name: str
    type: str  # S3, MONGODB, POSTGRESQL, FILESYSTEM
    configuration: Dict[str, Any]
    status: str = "active"
    priority: int = 1
    capacity: Optional[int] = None
    used_space: int = 0

class StorageBackendCreate(StorageBackendBase):
    """创建存储后端的请求模型"""
    pass

class StorageBackendUpdate(BaseModel):
    """更新存储后端的请求模型"""
    name: Optional[str] = None
    type: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    capacity: Optional[int] = None
    used_space: Optional[int] = None

class StorageBackendInDB(StorageBackendBase):
    """数据库中的存储后端模型"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class StorageBackendResponse(StorageBackendInDB):
    """存储后端响应模型"""
    pass

class StorageBackendList(BaseModel):
    """存储后端列表响应模型"""
    backends: List[StorageBackendResponse]
    total: int 