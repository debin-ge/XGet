from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ActivityType(str, Enum):
    """活动类型枚举"""
    ACCOUNT_LOGIN = "ACCOUNT_LOGIN"
    PROXY_USAGE = "PROXY_USAGE"
    TASK_EXECUTION = "TASK_EXECUTION"


class AnalyticsResponse(BaseModel):
    """分析响应基础模型"""
    success: bool = Field(description="请求是否成功")
    message: str = Field(description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")


class RealtimeAnalyticsData(BaseModel):
    """实时分析数据"""
    active_accounts: int = Field(description="活跃账户数量")
    login_success_rate: float = Field(description="登录成功率 (0-1)")
    avg_response_time: float = Field(description="平均响应时间 (秒)")
    last_updated: datetime = Field(description="数据最后更新时间")


class HistoryAnalyticsData(BaseModel):
    """历史分析数据"""
    time_range: str = Field(description="时间范围")
    trends: List[Dict[str, Any]] = Field(description="趋势数据")
    health_metrics: Dict[str, Any] = Field(description="健康度指标")


class AccountUsageStats(BaseModel):
    """账户使用统计"""
    account_id: Optional[str] = Field(None, description="账户ID")
    username: Optional[str] = Field(None, description="用户名")
    total_logins: int = Field(description="总登录次数")
    successful_logins: int = Field(description="成功登录次数")
    failed_logins: int = Field(description="失败登录次数")
    success_rate: float = Field(description="成功率 (0-1)")
    avg_response_time: float = Field(description="平均响应时间 (秒)")
    last_login_time: Optional[datetime] = Field(None, description="最后登录时间")
    days_since_last_login: Optional[int] = Field(None, description="距离最后登录天数")


class AccountSummaryStats(BaseModel):
    """账户汇总统计"""
    total_accounts: int = Field(description="总账户数")
    active_accounts: int = Field(description="活跃账户数")
    inactive_accounts: int = Field(description="非活跃账户数")
    accounts_with_errors: int = Field(description="有错误的账户数")
    average_success_rate: float = Field(description="平均成功率 (0-1)")
    average_response_time: float = Field(description="平均响应时间 (秒)")
    inactive_days_threshold: int = Field(description="非活跃天数阈值")


class RecentActivity(BaseModel):
    """最近活动"""
    id: str = Field(description="活动ID")
    type: ActivityType = Field(description="活动类型")
    timestamp: datetime = Field(description="活动时间戳")
    description: str = Field(description="活动描述")
    status: str = Field(description="活动状态")
    details: Dict[str, Any] = Field(description="活动详情")
    service: str = Field(description="相关服务")


class HealthMetrics(BaseModel):
    """健康度指标"""
    total_accounts: int = Field(description="总账户数")
    active_accounts: int = Field(description="活跃账户数")
    error_accounts: int = Field(description="错误账户数")
    health_score: float = Field(description="健康度分数 (0-100)")


class LoginTrendData(BaseModel):
    """登录趋势数据"""
    time_bucket: datetime = Field(description="时间分桶")
    total_logins: int = Field(description="总登录次数")
    successful_logins: int = Field(description="成功登录次数")
    failed_logins: int = Field(description="失败登录次数")
    success_rate: float = Field(description="成功率 (0-1)")
    avg_response_time: float = Field(description="平均响应时间 (秒)")