import json
import logging
from typing import Dict, Any, Optional, List, Union
import hashlib
from datetime import datetime
import motor.motor_asyncio
from bson import ObjectId
from .base import StorageBackendBase
from ..core.config import settings
from ..db.database import mongo_client

logger = logging.getLogger(__name__)

class MongoDBBackend(StorageBackendBase):
    """MongoDB存储后端实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化MongoDB存储后端
        
        Args:
            config: 配置信息，包括uri, database, collection
        """
        self.uri = config.get("uri", settings.MONGODB_URI)
        self.database_name = config.get("database", "storage")
        self.collection_name = config.get("collection", "data")
        self.client = None
        self.db = None
        self.collection = None
    
    async def initialize(self) -> bool:
        """
        初始化MongoDB客户端
        
        Returns:
            初始化是否成功
        """
        try:
            # 使用全局MongoDB客户端或创建新客户端
            if mongo_client:
                self.client = mongo_client
            else:
                self.client = motor.motor_asyncio.AsyncIOMotorClient(self.uri)
            
            # 获取数据库和集合
            self.db = self.client.get_database(self.database_name)
            self.collection = self.db[self.collection_name]
            
            # 创建索引
            await self.collection.create_index("key", unique=True)
            await self.collection.create_index("content_hash")
            await self.collection.create_index("created_at")
            
            logger.info(f"MongoDB存储后端初始化成功: {self.database_name}/{self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"MongoDB存储后端初始化失败: {str(e)}")
            return False
    
    async def store(self, key: str, data: Union[bytes, str, Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        存储数据到MongoDB
        
        Args:
            key: 存储键
            data: 要存储的数据
            metadata: 元数据
            
        Returns:
            存储结果信息
        """
        if self.collection is None:
            await self.initialize()
        
        try:
            # 准备数据
            if isinstance(data, bytes):
                # 二进制数据转为Base64字符串
                import base64
                data_str = base64.b64encode(data).decode("utf-8")
                content_type = "application/octet-stream"
                is_binary = True
            elif isinstance(data, str):
                data_str = data
                content_type = "text/plain"
                is_binary = False
            else:
                # 字典或其他对象
                data_str = json.dumps(data) if not isinstance(data, str) else data
                content_type = "application/json"
                is_binary = False
            
            # 计算大小和哈希
            size = len(data_str)
            content_hash = hashlib.md5(data_str.encode("utf-8") if isinstance(data_str, str) else data).hexdigest()
            
            # 准备文档
            document = {
                "key": key,
                "data": data_str,
                "is_binary": is_binary,
                "content_type": content_type,
                "size": size,
                "content_hash": content_hash,
                "metadata": metadata or {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # 插入或更新文档
            result = await self.collection.replace_one(
                {"key": key},
                document,
                upsert=True
            )
            
            # 返回存储结果
            return {
                "key": key,
                "size": size,
                "content_hash": content_hash,
                "storage_location": f"mongodb://{self.database_name}/{self.collection_name}/{key}",
                "metadata": metadata,
                "timestamp": datetime.utcnow().isoformat(),
                "upserted_id": str(result.upserted_id) if result.upserted_id else None,
                "modified_count": result.modified_count
            }
        except Exception as e:
            logger.error(f"MongoDB存储失败: {str(e)}")
            raise
    
    async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """
        从MongoDB检索数据
        
        Args:
            key: 存储键
            
        Returns:
            检索到的数据和元数据
        """
        if self.collection is None:
            await self.initialize()
        
        try:
            # 查询文档
            document = await self.collection.find_one({"key": key})
            
            if not document:
                return None
            
            # 处理二进制数据
            if document.get("is_binary", False):
                import base64
                data = base64.b64decode(document["data"])
            elif document.get("content_type") == "application/json":
                # 尝试解析JSON
                try:
                    data = json.loads(document["data"])
                except json.JSONDecodeError:
                    data = document["data"]
            else:
                data = document["data"]
            
            # 返回结果
            return {
                "key": key,
                "data": data,
                "metadata": document.get("metadata", {}),
                "size": document.get("size", 0),
                "content_type": document.get("content_type", ""),
                "content_hash": document.get("content_hash", ""),
                "created_at": document.get("created_at"),
                "updated_at": document.get("updated_at")
            }
        except Exception as e:
            logger.error(f"MongoDB检索失败: {str(e)}")
            return None
    
    async def delete(self, key: str) -> bool:
        """
        从MongoDB删除数据
        
        Args:
            key: 存储键
            
        Returns:
            删除是否成功
        """
        if self.collection is None:
            await self.initialize()
        
        try:
            result = await self.collection.delete_one({"key": key})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"MongoDB删除失败: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        检查MongoDB文档是否存在
        
        Args:
            key: 存储键
            
        Returns:
            文档是否存在
        """
        if self.collection is None:
            await self.initialize()
        
        try:
            count = await self.collection.count_documents({"key": key}, limit=1)
            return count > 0
        except Exception as e:
            logger.error(f"MongoDB检查文档存在失败: {str(e)}")
            return False
    
    async def list_keys(self, prefix: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[str]:
        """
        列出MongoDB中的键
        
        Args:
            prefix: 键前缀
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            键列表
        """
        if self.collection is None:
            await self.initialize()
        
        try:
            # 构建查询
            query = {}
            if prefix:
                query["key"] = {"$regex": f"^{prefix}"}
            
            # 执行查询
            cursor = self.collection.find(query, {"key": 1})
            cursor = cursor.skip(offset).limit(limit)
            
            # 提取键
            documents = await cursor.to_list(length=limit)
            return [doc["key"] for doc in documents]
        except Exception as e:
            logger.error(f"MongoDB列出键失败: {str(e)}")
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取MongoDB存储统计信息
        
        Returns:
            统计信息
        """
        if self.collection is None:
            await self.initialize()
        
        try:
            # 获取文档总数
            total_documents = await self.collection.count_documents({})
            
            # 获取总大小
            pipeline = [
                {"$group": {"_id": None, "total_size": {"$sum": "$size"}}}
            ]
            result = await self.collection.aggregate(pipeline).to_list(length=1)
            total_size = result[0]["total_size"] if result else 0
            
            # 按内容类型分组
            pipeline = [
                {"$group": {
                    "_id": "$content_type",
                    "count": {"$sum": 1},
                    "size": {"$sum": "$size"}
                }}
            ]
            content_types = await self.collection.aggregate(pipeline).to_list(length=100)
            content_type_stats = {
                doc["_id"]: {"count": doc["count"], "size": doc["size"]}
                for doc in content_types
            }
            
            return {
                "backend_type": "mongodb",
                "database": self.database_name,
                "collection": self.collection_name,
                "total_documents": total_documents,
                "total_size": total_size,
                "content_types": content_type_stats
            }
        except Exception as e:
            logger.error(f"MongoDB获取统计信息失败: {str(e)}")
            return {
                "backend_type": "mongodb",
                "database": self.database_name,
                "collection": self.collection_name,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        MongoDB健康检查
        
        Returns:
            健康状态信息
        """
        if self.collection is None:
            await self.initialize()
        
        try:
            # 检查连接
            await self.db.command("ping")
            
            # 尝试写入和读取测试文档
            test_key = f"health-check-{datetime.utcnow().timestamp()}"
            test_data = f"Health check at {datetime.utcnow().isoformat()}"
            
            # 存储测试数据
            await self.store(test_key, test_data)
            
            # 检索测试数据
            retrieved = await self.retrieve(test_key)
            
            # 删除测试数据
            await self.delete(test_key)
            
            # 验证测试结果
            if retrieved and retrieved.get("data") == test_data:
                return {
                    "status": "healthy",
                    "message": "MongoDB存储后端运行正常",
                    "backend_type": "mongodb",
                    "database": self.database_name,
                    "collection": self.collection_name
                }
            else:
                return {
                    "status": "warning",
                    "message": "MongoDB存储后端读写测试异常",
                    "backend_type": "mongodb",
                    "database": self.database_name,
                    "collection": self.collection_name
                }
        except Exception as e:
            logger.error(f"MongoDB健康检查失败: {str(e)}")
            return {
                "status": "unhealthy",
                "message": f"MongoDB存储后端异常: {str(e)}",
                "backend_type": "mongodb",
                "database": self.database_name,
                "collection": self.collection_name
            } 