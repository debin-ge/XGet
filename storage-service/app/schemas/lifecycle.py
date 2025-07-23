from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class LifecycleInfo(BaseModel):
    """生命周期信息模型"""
    retention_policy: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    accessed_at: Optional[datetime] = None
    status: str
    days_since_creation: int
    days_since_last_access: Optional[int] = None
    days_until_archive: Optional[int] = None
    days_until_deletion: Optional[int] = None

class LifecycleUpdate(BaseModel):
    """生命周期更新请求模型"""
    retention_policy: str
    
class LifecycleResponse(BaseModel):
    """生命周期响应模型"""
    item_id: str
    lifecycle_info: LifecycleInfo
    applied: bool
    message: Optional[str] = None 