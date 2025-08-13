from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Generic, TypeVar
from datetime import datetime
from .task import PaginatedResponse


class ResultBase(BaseModel):
    task_id: str
    data_type: str
    data: Any
    metadata: Optional[Dict[str, Any]] = None


class ResultCreate(ResultBase):
    pass


class ResultResponse(ResultBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ResultQuery(BaseModel):
    task_id: Optional[str] = None
    data_type: Optional[str] = None
    query: Optional[Dict[str, Any]] = None
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页数量")


class ResultsResponse(PaginatedResponse[ResultResponse]):
    """抓取结果分页响应"""
    pass

# 保持向后兼容的简单响应
class SimpleResultsResponse(BaseModel):
    total: int
    data: List[ResultResponse]
