from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Generic, TypeVar
from datetime import datetime
import uuid

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """通用分页响应模式"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    
    @classmethod
    def create(cls, items: List[T], total: int, page: int, size: int):
        """创建分页响应"""
        pages = (total + size - 1) // size if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )


class TaskBase(BaseModel):
    task_name: str
    describe: Optional[str] = None
    task_type: str
    parameters: Dict[str, Any]
    account_id: Optional[str] = None
    proxy_id: Optional[str] = None
    user_id: Optional[str] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    task_name: Optional[str] = None
    describe: Optional[str] = None
    task_type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    account_id: Optional[str] = None
    proxy_id: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None


class TaskResponse(TaskBase):
    id: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskStatusResponse(BaseModel):
    id: str
    task_name: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

# 新增分页响应类型
class TaskListResponse(PaginatedResponse[TaskResponse]):
    """任务列表分页响应"""
    pass
