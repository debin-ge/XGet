from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class ProcessingResultBase(BaseModel):
    """处理结果基础模型"""
    task_id: str
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    storage_location: Optional[str] = None

class ProcessingResultCreate(ProcessingResultBase):
    """创建处理结果的请求模型"""
    pass

class ProcessingResultUpdate(BaseModel):
    """更新处理结果的请求模型"""
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    storage_location: Optional[str] = None

class ProcessingResultInDB(ProcessingResultBase):
    """数据库中的处理结果模型"""
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProcessingResultResponse(ProcessingResultInDB):
    """处理结果响应模型"""
    pass

class ProcessingResultList(BaseModel):
    """处理结果列表响应模型"""
    results: List[ProcessingResultResponse]
    total: int 