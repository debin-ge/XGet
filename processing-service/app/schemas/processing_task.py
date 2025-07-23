from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4

class ProcessingTaskBase(BaseModel):
    """处理任务基础模型"""
    task_type: str
    source_data_id: str
    parameters: Optional[Dict[str, Any]] = None
    priority: str = "normal"
    callback_url: Optional[str] = None

class ProcessingTaskCreate(ProcessingTaskBase):
    """创建处理任务的请求模型"""
    pass

class ProcessingTaskUpdate(BaseModel):
    """更新处理任务的请求模型"""
    parameters: Optional[Dict[str, Any]] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[float] = None
    error_message: Optional[str] = None
    result_id: Optional[str] = None

class ProcessingTaskInDB(ProcessingTaskBase):
    """数据库中的处理任务模型"""
    id: str
    status: str = "pending"
    progress: float = 0.0
    error_message: Optional[str] = None
    result_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ProcessingTaskResponse(ProcessingTaskInDB):
    """处理任务响应模型"""
    pass

class ProcessingTaskList(BaseModel):
    """处理任务列表响应模型"""
    tasks: List[ProcessingTaskResponse]
    total: int
    page: int
    page_size: int 