from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
import enum

class AnalyticsMetricBase(BaseModel):
    name: str = Field(..., max_length=100)
    category: str = Field(..., max_length=50)  # ACCOUNT, PROXY, TASK, RESULT
    calculation_type: str = Field(..., max_length=20)  # COUNT, SUM, AVG, MAX, MIN, CUSTOM
    data_source: str = Field(..., max_length=50)
    dimensions: List[str] = Field(default_factory=list)
    filters: Dict[str, Any] = Field(default_factory=dict)
    refresh_interval: int = Field(default=3600)
    is_active: bool = Field(default=True)


class AnalyticsResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class ActivityType(str, enum.Enum):
    ACCOUNT_LOGIN = "ACCOUNT_LOGIN"
    PROXY_USAGE = "PROXY_USAGE" 
    TASK_EXECUTION = "TASK_EXECUTION"


class RecentActivity(BaseModel):
    id: str
    type: ActivityType
    timestamp: datetime
    description: str
    status: str
    details: Dict[str, Any] = Field(default_factory=dict)
    service: str


class RecentActivitiesResponse(BaseModel):
    activities: List[RecentActivity]
    total_count: int
