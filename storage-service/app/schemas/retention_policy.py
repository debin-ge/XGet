from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class RetentionPolicyBase(BaseModel):
    """保留策略基础模型"""
    name: str
    description: Optional[str] = None
    active_period: int  # 活跃期（天）
    archive_period: int  # 归档期（天）
    total_retention: int  # 总保留期（天）
    auto_delete: bool = False

class RetentionPolicyCreate(RetentionPolicyBase):
    """创建保留策略的请求模型"""
    pass

class RetentionPolicyUpdate(BaseModel):
    """更新保留策略的请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    active_period: Optional[int] = None
    archive_period: Optional[int] = None
    total_retention: Optional[int] = None
    auto_delete: Optional[bool] = None

class RetentionPolicyInDB(RetentionPolicyBase):
    """数据库中的保留策略模型"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RetentionPolicyResponse(RetentionPolicyInDB):
    """保留策略响应模型"""
    pass

class RetentionPolicyList(BaseModel):
    """保留策略列表响应模型"""
    policies: List[RetentionPolicyResponse]
    total: int 