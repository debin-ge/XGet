from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class MetadataBase(BaseModel):
    """元数据基础模型"""
    item_id: str
    source_id: Optional[str] = None
    processing_id: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    retention_policy: Optional[str] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None

class MetadataCreate(MetadataBase):
    """创建元数据的请求模型"""
    pass

class MetadataUpdate(BaseModel):
    """更新元数据的请求模型"""
    source_id: Optional[str] = None
    processing_id: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    retention_policy: Optional[str] = None
    access_count: Optional[int] = None
    last_accessed: Optional[datetime] = None

class MetadataInDB(MetadataBase):
    """数据库中的元数据模型"""
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class MetadataResponse(MetadataInDB):
    """元数据响应模型"""
    pass 