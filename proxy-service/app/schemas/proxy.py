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
        orm_mode = True


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
