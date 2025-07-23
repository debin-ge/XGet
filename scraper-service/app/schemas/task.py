from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class TaskBase(BaseModel):
    task_type: str
    parameters: Dict[str, Any]
    account_id: str
    proxy_id: Optional[str] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[float] = None
    result_count: Optional[int] = None
    error_message: Optional[str] = None


class TaskResponse(TaskBase):
    id: str
    status: str
    progress: float
    result_count: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskStatusResponse(BaseModel):
    id: str
    status: str
    progress: float
    result_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
