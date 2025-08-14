from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .task import PaginatedResponse


class TaskExecutionBase(BaseModel):
    task_id: str
    account_id: Optional[str] = None
    proxy_id: Optional[str] = None
    status: str
    started_at: datetime


class TaskExecutionCreate(TaskExecutionBase):
    pass


class TaskExecutionUpdate(BaseModel):
    status: Optional[str] = None
    completed_at: Optional[datetime] = None
    duration: Optional[int] = None
    error_message: Optional[str] = None


class TaskExecutionResponse(TaskExecutionBase):
    id: str
    completed_at: Optional[datetime] = None
    duration: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True 

# 新增分页响应类型
class TaskExecutionListResponse(PaginatedResponse[TaskExecutionResponse]):
    """任务执行列表分页响应"""
    pass 