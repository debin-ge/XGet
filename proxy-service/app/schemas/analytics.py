from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class AnalyticsResponse(BaseModel):
    """分析响应基础模型"""
    success: bool = Field(description="请求是否成功")
    message: str = Field(description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")


class ProxyStatus(str, Enum):
    """代理状态枚举"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    CHECKING = "CHECKING"


class UsageStatus(str, Enum):
    """使用状态枚举"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


class RealtimeProxyAnalytics(BaseModel):
    """实时代理分析数据"""
    total_proxies: int = Field(description="总代理数量")
    active_proxies: int = Field(description="活跃代理数量")
    success_rate: float = Field(description="成功率 (0-1)")
    avg_latency: float = Field(description="平均延迟 (毫秒)")
    avg_response_time: float = Field(description="平均响应时间 (毫秒)")
    last_updated: datetime = Field(description="数据最后更新时间")


class ProxyTrendData(BaseModel):
    """代理趋势数据"""
    time_bucket: datetime = Field(description="时间分桶")
    total_requests: int = Field(description="总请求数")
    successful_requests: int = Field(description="成功请求数")
    failed_requests: int = Field(description="失败请求数")
    success_rate: float = Field(description="成功率 (0-1)")
    avg_response_time: float = Field(description="平均响应时间 (毫秒)")
    avg_latency: float = Field(description="平均延迟 (毫秒)")


class GeographicDistribution(BaseModel):
    """地理分布数据"""
    country: str = Field(description="国家代码")
    total_proxies: int = Field(description="总代理数")
    active_proxies: int = Field(description="活跃代理数")
    avg_success_rate: float = Field(description="平均成功率 (0-1)")
    avg_response_time: float = Field(description="平均响应时间 (毫秒)")
    avg_latency: float = Field(description="平均延迟 (毫秒)")
    total_usage: int = Field(description="总使用次数")
    successful_usage: int = Field(description="成功使用次数")


class ISPDistribution(BaseModel):
    """ISP分布数据"""
    isp: str = Field(description="ISP名称")
    total_proxies: int = Field(description="总代理数")
    active_proxies: int = Field(description="活跃代理数")
    avg_success_rate: float = Field(description="平均成功率 (0-1)")
    avg_response_time: float = Field(description="平均响应时间 (毫秒)")
    avg_latency: float = Field(description="平均延迟 (毫秒)")
    total_usage: int = Field(description="总使用次数")
    successful_usage: int = Field(description="成功使用次数")


class HistoryProxyAnalytics(BaseModel):
    """历史代理分析数据"""
    time_range: str = Field(description="时间范围")
    trends: List[ProxyTrendData] = Field(description="趋势数据")
    geographic_distribution: List[GeographicDistribution] = Field(description="地理分布")
    isp_distribution: List[ISPDistribution] = Field(description="ISP分布")


class ProxyQualityStats(BaseModel):
    """单个代理质量统计"""
    proxy_id: str = Field(description="代理ID")
    ip: str = Field(description="IP地址")
    port: int = Field(description="端口")
    country: Optional[str] = Field(None, description="国家")
    city: Optional[str] = Field(None, description="城市")
    isp: Optional[str] = Field(None, description="ISP")
    status: ProxyStatus = Field(description="代理状态")
    success_rate: float = Field(description="成功率 (0-1)")
    latency: Optional[float] = Field(None, description="延迟 (毫秒)")
    total_usage: int = Field(description="总使用次数")
    successful_usage: int = Field(description="成功使用次数")
    failed_usage: int = Field(description="失败使用次数")
    avg_response_time: float = Field(description="平均响应时间 (毫秒)")
    quality_score: float = Field(description="质量分数 (0-1)")
    last_used: Optional[datetime] = Field(None, description="最后使用时间")
    last_check: Optional[datetime] = Field(None, description="最后检查时间")


class ProxyQualitySummary(BaseModel):
    """代理质量汇总统计"""
    total_proxies: int = Field(description="总代理数")
    active_proxies: int = Field(description="活跃代理数")
    avg_success_rate: float = Field(description="平均成功率 (0-1)")
    avg_quality_score: float = Field(description="平均质量分数 (0-1)")
    avg_latency: float = Field(description="平均延迟 (毫秒)")
    avg_response_time: float = Field(description="平均响应时间 (毫秒)")
    quality_distribution: Dict[str, int] = Field(description="质量分数分布")


class ProxyQualityDistribution(BaseModel):
    """代理质量分布"""
    excellent: int = Field(description="优秀代理数 (0.8-1.0)")
    good: int = Field(description="良好代理数 (0.6-0.8)")
    fair: int = Field(description="一般代理数 (0.4-0.6)")
    poor: int = Field(description="较差代理数 (0.0-0.4)")


class RecentProxyActivity(BaseModel):
    """最近代理活动"""
    id: str = Field(description="活动ID")
    proxy_id: str = Field(description="代理ID")
    proxy_ip: str = Field(description="代理IP")
    proxy_port: int = Field(description="代理端口")
    timestamp: datetime = Field(description="活动时间戳")
    status: UsageStatus = Field(description="使用状态")
    response_time: Optional[int] = Field(None, description="响应时间 (毫秒)")
    latency: Optional[int] = Field(None, description="延迟 (毫秒)")
    account_id: Optional[str] = Field(None, description="账户ID")
    task_id: Optional[str] = Field(None, description="任务ID")
    service_name: Optional[str] = Field(None, description="服务名称")
    success: bool = Field(description="是否成功")
    description: str = Field(description="活动描述")