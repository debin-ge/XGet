from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class AnalyticsResponse(BaseModel):
    """分析响应基础模型"""
    success: bool = Field(description="请求是否成功")
    message: str = Field(description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


class ExecutionStatus(str, Enum):
    """执行状态枚举"""
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TimeGranularity(str, Enum):
    """时间粒度枚举"""
    MINUTE = "MINUTE"
    HOUR = "HOUR"
    DAY = "DAY"


class RealtimeTaskAnalytics(BaseModel):
    """实时任务分析数据"""
    total_tasks: int = Field(description="总任务数")
    completed_tasks: int = Field(description="已完成任务数")
    failed_tasks: int = Field(description="失败任务数")
    success_rate: float = Field(description="成功率 (0-1)")
    avg_duration: float = Field(description="平均执行时间 (秒)")
    last_updated: datetime = Field(description="数据最后更新时间")


class TaskEfficiencyTrend(BaseModel):
    """任务效率趋势数据"""
    time_bucket: datetime = Field(description="时间分桶")
    total_executions: int = Field(description="总执行次数")
    successful_executions: int = Field(description="成功执行次数")
    failed_executions: int = Field(description="失败执行次数")
    success_rate: float = Field(description="成功率 (0-1)")
    avg_duration: float = Field(description="平均执行时间 (秒)")


class TaskErrorAnalysis(BaseModel):
    """任务错误分析"""
    error_message: str = Field(description="错误信息")
    error_count: int = Field(description="错误次数")
    error_percentage: float = Field(description="错误百分比 (0-100)")


class TaskTypeDistribution(BaseModel):
    """任务类型分布"""
    task_type: str = Field(description="任务类型")
    total_executions: int = Field(description="总执行次数")
    successful_executions: int = Field(description="成功执行次数")
    failed_executions: int = Field(description="失败执行次数")
    success_rate: float = Field(description="成功率 (0-1)")
    avg_duration: float = Field(description="平均执行时间 (秒)")


class HistoryTaskAnalytics(BaseModel):
    """历史任务分析数据"""
    time_range: str = Field(description="时间范围")
    efficiency_trends: List[TaskEfficiencyTrend] = Field(description="效率趋势数据")
    error_analysis: List[TaskErrorAnalysis] = Field(description="错误分析数据")
    type_distribution: List[TaskTypeDistribution] = Field(description="类型分布数据")


class TaskExecutionStats(BaseModel):
    """单个任务执行统计"""
    task_id: str = Field(description="任务ID")
    task_name: str = Field(description="任务名称")
    task_type: str = Field(description="任务类型")
    total_executions: int = Field(description="总执行次数")
    completed_executions: int = Field(description="成功执行次数")
    failed_executions: int = Field(description="失败执行次数")
    running_executions: int = Field(description="正在执行的次数")
    success_rate: float = Field(description="成功率 (0-1)")
    avg_duration: float = Field(description="平均执行时间 (秒)")
    unique_accounts: int = Field(description="使用的不同账户数")
    unique_proxies: int = Field(description="使用的不同代理数")
    last_execution: Optional[datetime] = Field(None, description="最后执行时间")


class TaskEfficiencySummary(BaseModel):
    """任务效率汇总"""
    task_id: Optional[str] = Field(None, description="任务ID")
    period: str = Field(description="统计周期")
    total_executions: int = Field(description="总执行次数")
    completed_executions: int = Field(description="成功执行次数")
    failed_executions: int = Field(description="失败执行次数")
    success_rate: float = Field(description="成功率 (0-1)")
    avg_duration: float = Field(description="平均执行时间 (秒)")
    unique_accounts: int = Field(description="使用的不同账户数")
    unique_proxies: int = Field(description="使用的不同代理数")


class TaskTrendSeries(BaseModel):
    """任务趋势系列数据"""
    name: str = Field(description="系列名称")
    data: List[int] = Field(description="数据点")
    type: str = Field(default="line", description="图表类型")
    smooth: bool = Field(default=True, description="是否平滑")


class TaskTrendData(BaseModel):
    """任务趋势图表数据"""
    x_axis: List[str] = Field(description="X轴数据（时间标签）")
    series: List[TaskTrendSeries] = Field(description="系列数据")
    summary: Dict[str, Any] = Field(description="汇总统计信息")


class RecentTaskActivity(BaseModel):
    """最近任务活动"""
    id: str = Field(description="活动ID")
    type: str = Field(default="TASK_EXECUTION", description="活动类型")
    timestamp: datetime = Field(description="活动时间戳")
    description: str = Field(description="活动描述")
    status: str = Field(description="活动状态")
    details: Dict[str, Any] = Field(description="活动详情")
    service: str = Field(default="scraper-service", description="相关服务")
    task_id: str = Field(description="任务ID")
    task_name: str = Field(description="任务名称")
    task_type: str = Field(description="任务类型")
    execution_id: str = Field(description="执行ID")
    account_id: Optional[str] = Field(None, description="账户ID")
    proxy_id: Optional[str] = Field(None, description="代理ID")
    duration: Optional[float] = Field(None, description="执行时长（秒）")