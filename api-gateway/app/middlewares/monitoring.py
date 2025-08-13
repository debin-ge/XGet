from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.core import CollectorRegistry
from fastapi.responses import Response as FastAPIResponse
import time
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)

# 创建自定义注册表
registry = CollectorRegistry()

# 定义指标
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=registry
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=registry
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Active HTTP requests',
    registry=registry
)

SERVICE_REQUESTS = Counter(
    'service_requests_total',
    'Total requests to backend services',
    ['service', 'status_code'],
    registry=registry
)

SERVICE_DURATION = Histogram(
    'service_request_duration_seconds',
    'Backend service request duration in seconds',
    ['service'],
    registry=registry
)

RATE_LIMIT_HITS = Counter(
    'rate_limit_hits_total',
    'Total rate limit hits',
    ['endpoint'],
    registry=registry
)


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.enabled = settings.METRICS_ENABLED
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """记录HTTP请求指标"""
        if not self.enabled:
            return
            
        try:
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
        except Exception as e:
            logger.error(f"记录请求指标失败: {str(e)}")
    
    def record_service_request(self, service: str, status_code: int, duration: float):
        """记录后端服务请求指标"""
        if not self.enabled:
            return
            
        try:
            SERVICE_REQUESTS.labels(
                service=service,
                status_code=status_code
            ).inc()
            
            SERVICE_DURATION.labels(service=service).observe(duration)
            
        except Exception as e:
            logger.error(f"记录服务请求指标失败: {str(e)}")
    
    def record_rate_limit_hit(self, endpoint: str):
        """记录限流命中"""
        if not self.enabled:
            return
            
        try:
            RATE_LIMIT_HITS.labels(endpoint=endpoint).inc()
        except Exception as e:
            logger.error(f"记录限流指标失败: {str(e)}")
    
    def increment_active_requests(self):
        """增加活跃请求数"""
        if self.enabled:
            ACTIVE_REQUESTS.inc()
    
    def decrement_active_requests(self):
        """减少活跃请求数"""
        if self.enabled:
            ACTIVE_REQUESTS.dec()


# 全局指标收集器实例
metrics_collector = MetricsCollector()


async def monitoring_middleware(request: Request, call_next):
    """监控中间件"""
    # 检查是否是指标端点
    if request.url.path == settings.METRICS_PATH:
        metrics_data = generate_latest(registry)
        return FastAPIResponse(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
    
    if not settings.METRICS_ENABLED:
        return await call_next(request)
    
    # 增加活跃请求计数
    metrics_collector.increment_active_requests()
    
    start_time = time.time()
    status_code = 500  # 默认状态码
    
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as e:
        logger.error(f"请求处理异常: {str(e)}")
        status_code = 500
        raise
    finally:
        # 计算请求耗时
        duration = time.time() - start_time
        
        # 简化端点路径用于指标标签
        endpoint = simplify_endpoint(request.url.path)
        
        # 记录指标
        metrics_collector.record_request(
            method=request.method,
            endpoint=endpoint,
            status_code=status_code,
            duration=duration
        )
        
        # 减少活跃请求计数
        metrics_collector.decrement_active_requests()


def simplify_endpoint(path: str) -> str:
    """简化端点路径，避免高基数标签"""
    # 移除API版本前缀
    if path.startswith("/api/v1"):
        path = path[7:]
    
    # 替换ID等动态部分
    parts = path.split("/")
    simplified_parts = []
    
    for part in parts:
        if not part:
            continue
        # 如果是UUID或者数字ID，替换为占位符
        if (len(part) == 36 and "-" in part) or part.isdigit():
            simplified_parts.append("{id}")
        else:
            simplified_parts.append(part)
    
    return "/" + "/".join(simplified_parts) if simplified_parts else "/"


def get_metrics_response():
    """获取指标响应"""
    if not settings.METRICS_ENABLED:
        return FastAPIResponse(
            content="Metrics disabled",
            status_code=404
        )
    
    metrics_data = generate_latest(registry)
    return FastAPIResponse(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST
    ) 