from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class StorageItemBase(BaseModel):
    """存储项基础模型"""
    data_type: str
    content_hash: Optional[str] = None
    size: Optional[int] = None
    storage_location: Optional[str] = None
    storage_backend: Optional[str] = None
    compression: bool = False
    encryption: bool = False
    version: int = 1
    status: str = "stored"

class StorageItemCreate(StorageItemBase):
    """创建存储项的请求模型"""
    pass

class StorageItemUpdate(BaseModel):
    """更新存储项的请求模型"""
    data_type: Optional[str] = None
    content_hash: Optional[str] = None
    size: Optional[int] = None
    storage_location: Optional[str] = None
    storage_backend: Optional[str] = None
    compression: Optional[bool] = None
    encryption: Optional[bool] = None
    version: Optional[int] = None
    status: Optional[str] = None
    accessed_at: Optional[datetime] = None

class StorageItemInDB(StorageItemBase):
    """数据库中的存储项模型"""
    id: str
    created_at: datetime
    updated_at: datetime
    accessed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class StorageItemResponse(StorageItemInDB):
    """存储项响应模型"""
    pass

class StorageItemList(BaseModel):
    """存储项列表响应模型"""
    items: List[StorageItemResponse]
    total: int
    page: int
    page_size: int 