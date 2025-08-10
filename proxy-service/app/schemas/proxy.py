from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProxyBase(BaseModel):
    type: str
    ip: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None


class ProxyCreate(ProxyBase):
    pass


class ProxyUpdate(BaseModel):
    type: Optional[str] = None
    ip: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    isp: Optional[str] = None
    latency: Optional[int] = None
    success_rate: Optional[float] = None
    status: Optional[str] = None


class ProxyQualityBase(BaseModel):
    total_usage: int
    success_count: int
    quality_score: float
    last_used: Optional[datetime] = None
    cooldown_time: int


class ProxyQualityCreate(BaseModel):
    proxy_id: str
    total_usage: int = 0
    success_count: int = 0
    quality_score: float = 0.8
    last_used: Optional[datetime] = None
    cooldown_time: int = 0


class ProxyQualityUpdate(BaseModel):
    total_usage: Optional[int] = None
    success_count: Optional[int] = None
    quality_score: Optional[float] = None
    last_used: Optional[datetime] = None
    cooldown_time: Optional[int] = None


class ProxyQualityResponse(ProxyQualityBase):
    id: str
    proxy_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProxyResponse(ProxyBase):
    id: str
    isp: Optional[str] = None
    latency: Optional[int] = None
    success_rate: float
    last_check: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProxyWithQualityResponse(ProxyResponse):
    """包含质量信息的代理响应"""
    quality: Optional[ProxyQualityResponse] = None

    class Config:
        from_attributes = True


class ProxyCheck(BaseModel):
    proxy_ids: List[str]


class ProxyCheckResult(BaseModel):
    id: str
    status: str
    latency: Optional[int] = None
    success_rate: Optional[float] = None
    error_msg: Optional[str] = None


class ProxyCheckResponse(BaseModel):
    total: int
    checked: int
    active: int
    inactive: int
    results: List[ProxyCheckResult]


class ProxyImport(BaseModel):
    proxies: List[ProxyCreate]
    check_availability: bool = True


class ProxyImportResult(BaseModel):
    id: str
    type: str
    ip: str
    status: str


class ProxyImportResponse(BaseModel):
    total: int
    imported: int
    active: int
    inactive: int
    proxies: List[ProxyImportResult]


class ProxyUsageResult(BaseModel):
    success: bool
    error_msg: Optional[str] = None


# 代理使用历史记录相关的schema
class ProxyUsageHistoryCreate(BaseModel):
    proxy_id: str
    user_id: Optional[str] = None
    service_name: Optional[str] = None
    success: str = "SUCCESS"  # SUCCESS, FAILED, TIMEOUT
    response_time: Optional[int] = None


class ProxyUsageHistoryResponse(BaseModel):
    id: str
    proxy_id: str
    user_id: Optional[str] = None
    service_name: Optional[str] = None
    success: str
    response_time: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProxyUsageHistoryListResponse(BaseModel):
    total: int
    items: List[ProxyUsageHistoryResponse]
    page: int
    size: int


class ProxyUsageHistoryFilter(BaseModel):
    proxy_id: Optional[str] = None
    user_id: Optional[str] = None
    service_name: Optional[str] = None
    success: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    size: int = 20
