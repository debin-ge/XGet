import redis.asyncio as redis
from redis.exceptions import RedisError
from typing import Optional, Any, Dict, List
import json
import logging
from .config import settings

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis连接管理工具类"""
    
    _pool: Optional[redis.ConnectionPool] = None
    _client: Optional[redis.Redis] = None
    
    @classmethod
    async def get_client(cls) -> redis.Redis:
        """获取Redis客户端实例"""
        if cls._client is None:
            await cls._initialize()
        return cls._client
    
    @classmethod
    async def _initialize(cls):
        """初始化Redis连接"""
        try:
            cls._pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=10,
                socket_timeout=5
            )
            cls._client = redis.Redis(connection_pool=cls._pool)
            await cls._client.ping()
            logger.info("Redis connection established successfully")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    @classmethod
    async def close(cls):
        """关闭Redis连接"""
        if cls._client:
            await cls._client.close()
        if cls._pool:
            await cls._pool.disconnect()
    
    @classmethod
    async def set_json(cls, key: str, value: Any, expire: int = 300) -> bool:
        """设置JSON格式的缓存"""
        try:
            client = await cls.get_client()
            serialized = json.dumps(value, ensure_ascii=False)
            return await client.setex(key, expire, serialized)
        except RedisError as e:
            logger.warning(f"Redis set_json failed: {e}")
            return False
    
    @classmethod
    async def get_json(cls, key: str) -> Optional[Any]:
        """获取JSON格式的缓存"""
        try:
            client = await cls.get_client()
            data = await client.get(key)
            return json.loads(data) if data else None
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Redis get_json failed: {e}")
            return None
    
    @classmethod
    async def delete_keys(cls, pattern: str) -> int:
        """删除匹配模式的键"""
        try:
            client = await cls.get_client()
            keys = await client.keys(pattern)
            if keys:
                return await client.delete(*keys)
            return 0
        except RedisError as e:
            logger.warning(f"Redis delete_keys failed: {e}")
            return 0
    
    @classmethod
    async def exists(cls, key: str) -> bool:
        """检查键是否存在"""
        try:
            client = await cls.get_client()
            return await client.exists(key) > 0
        except RedisError as e:
            logger.warning(f"Redis exists failed: {e}")
            return False