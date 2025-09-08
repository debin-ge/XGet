from functools import wraps
from typing import Callable, Optional, Any, Union
import hashlib
import json
from datetime import timedelta
from decimal import Decimal

import redis.asyncio as redis

from app.core.config import settings


class DecimalEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理Decimal类型"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class RedisCache:
    """Redis缓存工具类"""
    
    def __init__(self):
        self.redis_client = None
    
    async def connect(self):
        """连接Redis"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            print("Redis connection established successfully")
            return True
        except Exception as e:
            print(f"Redis connection failed: {e}")
            return False
    
    async def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            if expire:
                await self.redis_client.setex(
                    key, 
                    timedelta(seconds=expire), 
                    json.dumps(value, cls=DecimalEncoder)
                )
            else:
                await self.redis_client.set(key, json.dumps(value, cls=DecimalEncoder))
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return await self.redis_client.exists(key) == 1
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """递增计数器"""
        try:
            return await self.redis_client.incrby(key, amount)
        except Exception as e:
            print(f"Redis increment error: {e}")
            return None
    
    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """递减计数器"""
        try:
            return await self.redis_client.decrby(key, amount)
        except Exception as e:
            print(f"Redis decrement error: {e}")
            return None
    
    async def get_keys(self, pattern: str = "*") -> list:
        """获取匹配模式的键"""
        try:
            return await self.redis_client.keys(pattern)
        except Exception as e:
            print(f"Redis keys error: {e}")
            return []
    
    async def flush_all(self) -> bool:
        """清空所有缓存"""
        try:
            await self.redis_client.flushall()
            return True
        except Exception as e:
            print(f"Redis flushall error: {e}")
            return False


def cache_response(expire: int = settings.CACHE_TTL, key_prefix: str = "cache"):
    """
    缓存API响应装饰器
    
    Args:
        expire: 缓存过期时间（秒）
        key_prefix: 缓存键前缀
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}"
            
            # 如果有关键参数，将其包含在缓存键中
            if kwargs:
                key_suffix = hashlib.md5(
                    json.dumps(kwargs, sort_keys=True).encode()
                ).hexdigest()
                cache_key = f"{cache_key}:{key_suffix}"
            
            # 尝试从缓存获取
            cached_result = await redis_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数获取结果
            result = await func(*args, **kwargs)
            
            # 缓存结果
            if result is not None:
                await redis_cache.set(cache_key, result, expire)
            
            return result
        
        return wrapper
    
    return decorator


# 全局Redis缓存实例
redis_cache = RedisCache()


async def init_redis():
    """初始化Redis连接"""
    return await redis_cache.connect()