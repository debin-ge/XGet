from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from ..core.config import settings
import time
import logging
from typing import Dict, Any
import hashlib

logger = logging.getLogger(__name__)


class RateLimiter:
    """基于Redis的分布式限流器"""
    
    def __init__(self):
        self.redis_client = None
        self.enabled = settings.RATE_LIMIT_ENABLED
        
    async def init_redis(self):
        """初始化Redis连接"""
        if not self.enabled:
            return
            
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            # 测试连接
            await self.redis_client.ping()
            logger.info("Redis连接成功，限流功能已启用")
        except Exception as e:
            logger.error(f"Redis连接失败，限流功能已禁用: {str(e)}")
            self.enabled = False
            self.redis_client = None
    
    async def close_redis(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
    
    def get_rate_limit_key(self, request: Request) -> str:
        """生成限流键"""
        # 使用IP地址和用户ID（如果有）作为限流依据
        client_ip = request.client.host
        user_info = getattr(request.state, "user", {})
        user_id = user_info.get("id", "anonymous")
        
        # 创建复合键
        key_data = f"{client_ip}:{user_id}:{request.url.path}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:16]
        
        return f"rate_limit:{key_hash}"
    
    async def is_allowed(self, request: Request) -> tuple[bool, Dict[str, Any]]:
        """
        检查请求是否被限流
        
        Returns:
            (is_allowed, rate_limit_info)
        """
        if not self.enabled or not self.redis_client:
            return True, {}
        
        try:
            rate_limit_key = self.get_rate_limit_key(request)
            current_time = int(time.time())
            window_start = current_time - settings.RATE_LIMIT_PERIOD_SECONDS
            
            # 使用滑动窗口算法
            pipe = self.redis_client.pipeline()
            
            # 移除过期的请求记录
            pipe.zremrangebyscore(rate_limit_key, 0, window_start)
            
            # 获取当前窗口内的请求数量
            pipe.zcard(rate_limit_key)
            
            # 添加当前请求
            pipe.zadd(rate_limit_key, {str(current_time): current_time})
            
            # 设置过期时间
            pipe.expire(rate_limit_key, settings.RATE_LIMIT_PERIOD_SECONDS + 1)
            
            results = await pipe.execute()
            current_requests = results[1]  # zcard的结果
            
            # 检查是否超过限制
            limit = settings.RATE_LIMIT_REQUESTS
            remaining = max(0, limit - current_requests - 1)  # -1 因为已经添加了当前请求
            reset_time = current_time + settings.RATE_LIMIT_PERIOD_SECONDS
            
            rate_limit_info = {
                "limit": limit,
                "remaining": remaining,
                "reset": reset_time,
                "reset_after": settings.RATE_LIMIT_PERIOD_SECONDS
            }
            
            if current_requests >= limit:
                return False, rate_limit_info
            
            return True, rate_limit_info
            
        except Exception as e:
            logger.error(f"限流检查失败: {str(e)}")
            # 如果Redis出错，允许请求通过
            return True, {}
    
    async def add_rate_limit_headers(self, response: JSONResponse, rate_limit_info: Dict[str, Any]):
        """添加限流相关的响应头"""
        if rate_limit_info:
            response.headers["X-RateLimit-Limit"] = str(rate_limit_info.get("limit", ""))
            response.headers["X-RateLimit-Remaining"] = str(rate_limit_info.get("remaining", ""))
            response.headers["X-RateLimit-Reset"] = str(rate_limit_info.get("reset", ""))
            response.headers["X-RateLimit-Reset-After"] = str(rate_limit_info.get("reset_after", ""))


# 全局限流器实例
rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """限流中间件"""
    # 检查是否允许请求
    is_allowed, rate_limit_info = await rate_limiter.is_allowed(request)
    
    if not is_allowed:
        # 返回限流错误
        response = JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Try again in {rate_limit_info.get('reset_after', 60)} seconds.",
                "rate_limit": rate_limit_info
            }
        )
        await rate_limiter.add_rate_limit_headers(response, rate_limit_info)
        return response
    
    # 处理请求
    response = await call_next(request)
    
    # 添加限流信息到响应头
    if isinstance(response, JSONResponse):
        await rate_limiter.add_rate_limit_headers(response, rate_limit_info)
    
    return response 