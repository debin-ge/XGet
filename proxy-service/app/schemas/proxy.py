from pydantic import BaseModel, Field
from typing import Optional, List, Generic, TypeVar
from datetime import datetime

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
    task_id: Optional[str] = None
    account_id: Optional[str] = None
    service_name: Optional[str] = None
    success: str = "SUCCESS"  # SUCCESS, FAILED, TIMEOUT
    response_time: Optional[int] = None
    
    proxy_ip: Optional[str] = None
    proxy_port: Optional[int] = None
    account_username_email: Optional[str] = None
    task_name: Optional[str] = None
    quality_score: Optional[float] = None
    latency: Optional[int] = None


class ProxyUsageHistoryResponse(BaseModel):
    id: str
    proxy_id: str
    # 原有字段
    account_id: Optional[str] = None
    task_id: Optional[str] = None
    service_name: Optional[str] = None
    success: str
    response_time: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # 冗余字段（直接存储，无需关联查询）
    proxy_ip: Optional[str] = None
    proxy_port: Optional[int] = None
    account_username_email: Optional[str] = None
    task_name: Optional[str] = None
    quality_score: Optional[float] = None
    latency: Optional[int] = None

    class Config:
        from_attributes = True


class ProxyUsageHistoryFilter(BaseModel):
    proxy_id: Optional[str] = None
    proxy_ip: Optional[str] = None
    account_email: Optional[str] = None
    task_name: Optional[str] = None
    service_name: Optional[str] = None
    success: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    size: int = 20

# 新增分页响应类型
class ProxyListResponse(PaginatedResponse[ProxyResponse]):
    """代理列表分页响应"""
    pass

class ProxyQualityListResponse(PaginatedResponse[ProxyQualityResponse]):
    """代理质量列表分页响应"""
    pass


class ProxyQualityInfoResponse(BaseModel):
    """代理质量信息综合响应 - 包含IP+port、检测成功率、使用次数、成功次数、质量分数、最近使用时间"""
    # 代理基本信息
    proxy_id: str
    ip: str
    port: int
    proxy_type: str
    
    # 质量信息
    total_usage: int = Field(description="总使用次数")
    success_count: int = Field(description="成功次数")
    success_rate: float = Field(description="检测成功率")
    quality_score: float = Field(description="质量分数")
    last_used: Optional[datetime] = Field(description="最近使用时间")
    
    # 其他信息
    status: str = Field(description="代理状态")
    country: Optional[str] = Field(description="国家")
    city: Optional[str] = Field(description="城市")
    isp: Optional[str] = Field(description="ISP")
    latency: Optional[int] = Field(description="延迟(毫秒)")
    created_at: datetime = Field(description="创建时间")
    updated_at: Optional[datetime] = Field(description="更新时间")

    class Config:
        from_attributes = True


class ProxyQualityInfoListResponse(PaginatedResponse[ProxyQualityInfoResponse]):
    """代理质量信息列表分页响应"""
    pass

class ProxyUsageHistoryListResponse(PaginatedResponse[ProxyUsageHistoryResponse]):
    """代理使用历史记录列表分页响应"""
    pass