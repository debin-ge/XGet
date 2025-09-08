from .task import (
    PaginatedResponse,
    TaskBase,
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskStatusResponse
)

from .task_execution import (
    TaskExecutionBase,
    TaskExecutionCreate,
    TaskExecutionUpdate,
    TaskExecutionResponse,
    TaskExecutionListResponse
)

from .result import (
    ResultResponse,
    ResultsResponse,
    SimpleResultsResponse
)

from .analytics import (
    AnalyticsResponse,
    TaskStatus,
    ExecutionStatus,
    TimeGranularity,
    RealtimeTaskAnalytics,
    TaskEfficiencyTrend,
    TaskErrorAnalysis,
    TaskTypeDistribution,
    HistoryTaskAnalytics,
    TaskExecutionStats,
    TaskEfficiencySummary,
    TaskTrendSeries,
    TaskTrendData,
    RecentTaskActivity
)

__all__ = [
    # Task schemas
    "PaginatedResponse",
    "TaskBase",
    "TaskCreate",
    "TaskUpdate", 
    "TaskResponse",
    "TaskListResponse",
    "TaskStatusResponse",
    # Task execution schemas
    "TaskExecutionBase",
    "TaskExecutionCreate",
    "TaskExecutionUpdate",
    "TaskExecutionResponse",
    "TaskExecutionListResponse",
    # Result schemas
    "ResultResponse",
    "ResultsResponse",
    "SimpleResultsResponse",
    # Analytics schemas
    "AnalyticsResponse",
    "TaskStatus",
    "ExecutionStatus",
    "TimeGranularity",
    "RealtimeTaskAnalytics",
    "TaskEfficiencyTrend",
    "TaskErrorAnalysis",
    "TaskTypeDistribution",
    "HistoryTaskAnalytics",
    "TaskExecutionStats",
    "TaskEfficiencySummary",
    "TaskTrendSeries",
    "TaskTrendData",
    "RecentTaskActivity"
]