from .proxy import (
    PaginatedResponse,
    ProxyBase,
    ProxyCreate,
    ProxyUpdate,
    ProxyResponse,
    ProxyListResponse,
    ProxyQualityResponse,
    ProxyQualityInfoResponse,
    ProxyQualityUpdate,
    ProxyCheckResult,
    ProxyCheckResponse,
    ProxyUsageHistoryResponse,
    ProxyUsageHistoryCreate,
    ProxyUsageResult
)

from .analytics import (
    AnalyticsResponse,
    ProxyStatus,
    UsageStatus,
    RealtimeProxyAnalytics,
    ProxyTrendData,
    GeographicDistribution,
    ISPDistribution,
    HistoryProxyAnalytics,
    ProxyQualityStats,
    ProxyQualitySummary,
    ProxyQualityDistribution,
    RecentProxyActivity
)

__all__ = [
    # Proxy schemas
    "PaginatedResponse",
    "ProxyBase",
    "ProxyCreate", 
    "ProxyUpdate",
    "ProxyResponse",
    "ProxyListResponse",
    "ProxyQualityResponse",
    "ProxyQualityInfoResponse",
    "ProxyQualityUpdate",
    "ProxyCheckResult",
    "ProxyCheckResponse",
    "ProxyUsageHistoryResponse",
    "ProxyUsageHistoryCreate",
    "ProxyUsageResult",
    # Analytics schemas
    "AnalyticsResponse",
    "ProxyStatus", 
    "UsageStatus",
    "RealtimeProxyAnalytics",
    "ProxyTrendData",
    "GeographicDistribution",
    "ISPDistribution",
    "HistoryProxyAnalytics",
    "ProxyQualityStats",
    "ProxyQualitySummary",
    "ProxyQualityDistribution",
    "RecentProxyActivity"
]