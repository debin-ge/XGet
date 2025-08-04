from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


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
    skip: int = 0
    limit: int = 100


class ResultsResponse(BaseModel):
    total: int
    data: List[ResultResponse]
