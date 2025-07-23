import logging
from typing import Dict, Any, Optional
from .base import StorageBackendBase
from .s3_backend import S3Backend
from .mongodb_backend import MongoDBBackend
from ..models.storage_backend import StorageBackend
from ..core.config import settings

logger = logging.getLogger(__name__)

class StorageBackendFactory:
    """存储后端工厂类，用于创建和管理不同类型的存储后端"""
    
    # 存储后端类型映射
    BACKEND_TYPES = {
        "S3": S3Backend,
        "MONGODB": MongoDBBackend,
    }
    
    # 缓存已创建的存储后端实例
    _instances = {}
    
    @classmethod
    async def create_backend(cls, backend_type: str, config: Dict[str, Any]) -> Optional[StorageBackendBase]:
        """
        创建存储后端实例
        
        Args:
            backend_type: 存储后端类型
            config: 配置信息
            
        Returns:
            存储后端实例
        """
        try:
            backend_class = cls.BACKEND_TYPES.get(backend_type.upper())
            if not backend_class:
                logger.error(f"不支持的存储后端类型: {backend_type}")
                return None
            
            # 创建实例
            backend = backend_class(config)
            
            # 初始化
            success = await backend.initialize()
            if not success:
                logger.error(f"存储后端初始化失败: {backend_type}")
                return None
            
            logger.info(f"创建存储后端: {backend_type}")
            return backend
        except Exception as e:
            logger.error(f"创建存储后端失败: {str(e)}")
            return None
    
    @classmethod
    async def get_backend(cls, backend_id: str, db_backend: StorageBackend = None) -> Optional[StorageBackendBase]:
        """
        获取存储后端实例，如果不存在则创建
        
        Args:
            backend_id: 存储后端ID或类型
            db_backend: 数据库中的存储后端记录
            
        Returns:
            存储后端实例
        """
        # 检查缓存
        if backend_id in cls._instances:
            return cls._instances[backend_id]
        
        try:
            if db_backend:
                # 使用数据库中的配置
                backend_type = db_backend.type
                config = db_backend.configuration
            else:
                # 使用默认配置
                if backend_id.upper() == "S3":
                    backend_type = "S3"
                    config = {
                        "endpoint": settings.MINIO_ENDPOINT,
                        "access_key": settings.MINIO_ROOT_USER,
                        "secret_key": settings.MINIO_ROOT_PASSWORD,
                        "secure": settings.MINIO_SECURE,
                        "bucket": settings.DEFAULT_BUCKET
                    }
                elif backend_id.upper() == "MONGODB":
                    backend_type = "MONGODB"
                    config = {
                        "uri": settings.MONGODB_URI,
                        "database": "storage",
                        "collection": "data"
                    }
                else:
                    logger.error(f"未知的存储后端ID: {backend_id}")
                    return None
            
            # 创建后端实例
            backend = await cls.create_backend(backend_type, config)
            if backend:
                # 缓存实例
                cls._instances[backend_id] = backend
            
            return backend
        except Exception as e:
            logger.error(f"获取存储后端失败: {str(e)}")
            return None
    
    @classmethod
    def clear_cache(cls):
        """清除后端实例缓存"""
        cls._instances.clear()
        logger.info("已清除存储后端缓存") 