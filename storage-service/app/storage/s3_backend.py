import json
import logging
import io
from typing import Dict, Any, Optional, List, Union
import hashlib
from datetime import datetime
import asyncio
from minio import Minio
from minio.error import S3Error
from .base import StorageBackendBase
from ..core.config import settings

logger = logging.getLogger(__name__)

class S3Backend(StorageBackendBase):
    """S3兼容存储后端实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化S3存储后端
        
        Args:
            config: 配置信息，包括endpoint, access_key, secret_key, secure, bucket
        """
        self.endpoint = config.get("endpoint", settings.MINIO_ENDPOINT)
        self.access_key = config.get("access_key", settings.MINIO_ROOT_USER)
        self.secret_key = config.get("secret_key", settings.MINIO_ROOT_PASSWORD)
        self.secure = config.get("secure", settings.MINIO_SECURE)
        self.bucket_name = config.get("bucket", settings.DEFAULT_BUCKET)
        self.client = None
    
    async def initialize(self) -> bool:
        """
        初始化S3客户端
        
        Returns:
            初始化是否成功
        """
        try:
            # 创建MinIO客户端
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
            
            # 确保存储桶存在
            loop = asyncio.get_event_loop()
            bucket_exists = await loop.run_in_executor(
                None, lambda: self.client.bucket_exists(self.bucket_name)
            )
            
            if not bucket_exists:
                await loop.run_in_executor(
                    None, lambda: self.client.make_bucket(self.bucket_name)
                )
                logger.info(f"创建存储桶: {self.bucket_name}")
            
            logger.info(f"S3存储后端初始化成功: {self.endpoint}/{self.bucket_name}")
            return True
        except S3Error as e:
            logger.error(f"S3存储后端初始化失败: {str(e)}")
            return False
    
    async def store(self, key: str, data: Union[bytes, str, Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        存储数据到S3
        
        Args:
            key: 存储键
            data: 要存储的数据
            metadata: 元数据
            
        Returns:
            存储结果信息
        """
        if self.client is None:
            await self.initialize()
        
        try:
            # 准备数据
            if isinstance(data, Dict):
                data_bytes = json.dumps(data).encode("utf-8")
                content_type = "application/json"
            elif isinstance(data, str):
                data_bytes = data.encode("utf-8")
                content_type = "text/plain"
            else:
                data_bytes = data
                content_type = "application/octet-stream"
            
            # 计算大小和哈希
            size = len(data_bytes)
            content_hash = hashlib.md5(data_bytes).hexdigest()
            
            # 准备元数据
            s3_metadata = {
                "Content-Type": content_type,
                "Content-Hash": content_hash,
            }
            
            if metadata:
                for k, v in metadata.items():
                    if isinstance(v, (str, int, float, bool)):
                        s3_metadata[k] = str(v)
            
            # 上传到S3
            data_stream = io.BytesIO(data_bytes)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.put_object(
                    self.bucket_name,
                    key,
                    data_stream,
                    size,
                    metadata=s3_metadata,
                    content_type=content_type
                )
            )
            
            # 返回存储结果
            return {
                "key": key,
                "size": size,
                "content_hash": content_hash,
                "storage_location": f"s3://{self.bucket_name}/{key}",
                "metadata": metadata,
                "timestamp": datetime.utcnow().isoformat()
            }
        except S3Error as e:
            logger.error(f"S3存储失败: {str(e)}")
            raise
    
    async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """
        从S3检索数据
        
        Args:
            key: 存储键
            
        Returns:
            检索到的数据和元数据
        """
        if self.client is None:
            await self.initialize()
        
        try:
            # 检查对象是否存在
            if not await self.exists(key):
                return None
            
            # 获取对象
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get_object(self.bucket_name, key)
            )
            
            # 读取数据
            data = await loop.run_in_executor(None, lambda: response.read())
            
            # 获取元数据
            metadata = {}
            for k, v in response.headers.items():
                if k.startswith("x-amz-meta-"):
                    metadata[k[11:]] = v
            
            # 尝试解析JSON
            content_type = response.headers.get("content-type", "")
            if content_type == "application/json":
                try:
                    data = json.loads(data.decode("utf-8"))
                except json.JSONDecodeError:
                    pass
            
            # 返回结果
            return {
                "key": key,
                "data": data,
                "metadata": metadata,
                "size": int(response.headers.get("content-length", 0)),
                "content_type": content_type,
                "last_modified": response.headers.get("last-modified"),
                "etag": response.headers.get("etag")
            }
        except S3Error as e:
            logger.error(f"S3检索失败: {str(e)}")
            return None
        finally:
            if 'response' in locals():
                await loop.run_in_executor(None, lambda: response.close())
                await loop.run_in_executor(None, lambda: response.release_conn())
    
    async def delete(self, key: str) -> bool:
        """
        从S3删除数据
        
        Args:
            key: 存储键
            
        Returns:
            删除是否成功
        """
        if self.client is None:
            await self.initialize()
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.remove_object(self.bucket_name, key)
            )
            return True
        except S3Error as e:
            logger.error(f"S3删除失败: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        检查S3对象是否存在
        
        Args:
            key: 存储键
            
        Returns:
            对象是否存在
        """
        if self.client is None:
            await self.initialize()
        
        try:
            loop = asyncio.get_event_loop()
            
            # 使用stat_object检查对象是否存在
            try:
                await loop.run_in_executor(
                    None,
                    lambda: self.client.stat_object(self.bucket_name, key)
                )
                return True
            except S3Error as e:
                if e.code == "NoSuchKey":
                    return False
                raise
        except Exception as e:
            logger.error(f"S3检查对象存在失败: {str(e)}")
            return False
    
    async def list_keys(self, prefix: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[str]:
        """
        列出S3中的键
        
        Args:
            prefix: 键前缀
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            键列表
        """
        if self.client is None:
            await self.initialize()
        
        try:
            loop = asyncio.get_event_loop()
            
            # 获取对象列表
            objects = await loop.run_in_executor(
                None,
                lambda: list(self.client.list_objects(
                    self.bucket_name,
                    prefix=prefix or "",
                    recursive=True
                ))
            )
            
            # 应用分页
            paginated_objects = objects[offset:offset + limit]
            
            # 提取键
            return [obj.object_name for obj in paginated_objects]
        except S3Error as e:
            logger.error(f"S3列出键失败: {str(e)}")
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取S3存储统计信息
        
        Returns:
            统计信息
        """
        if self.client is None:
            await self.initialize()
        
        try:
            loop = asyncio.get_event_loop()
            
            # 获取所有对象
            objects = await loop.run_in_executor(
                None,
                lambda: list(self.client.list_objects(
                    self.bucket_name,
                    recursive=True
                ))
            )
            
            # 计算统计信息
            total_objects = len(objects)
            total_size = sum(obj.size for obj in objects)
            
            # 按前缀分组
            prefixes = {}
            for obj in objects:
                parts = obj.object_name.split("/")
                if len(parts) > 1:
                    prefix = parts[0]
                    if prefix not in prefixes:
                        prefixes[prefix] = {"count": 0, "size": 0}
                    prefixes[prefix]["count"] += 1
                    prefixes[prefix]["size"] += obj.size
            
            return {
                "backend_type": "s3",
                "endpoint": self.endpoint,
                "bucket": self.bucket_name,
                "total_objects": total_objects,
                "total_size": total_size,
                "prefixes": prefixes
            }
        except S3Error as e:
            logger.error(f"S3获取统计信息失败: {str(e)}")
            return {
                "backend_type": "s3",
                "endpoint": self.endpoint,
                "bucket": self.bucket_name,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        S3健康检查
        
        Returns:
            健康状态信息
        """
        if self.client is None:
            await self.initialize()
        
        try:
            # 检查连接
            loop = asyncio.get_event_loop()
            bucket_exists = await loop.run_in_executor(
                None, lambda: self.client.bucket_exists(self.bucket_name)
            )
            
            if not bucket_exists:
                return {
                    "status": "warning",
                    "message": f"存储桶不存在: {self.bucket_name}",
                    "backend_type": "s3",
                    "endpoint": self.endpoint
                }
            
            # 尝试写入和读取测试对象
            test_key = f"health-check-{datetime.utcnow().timestamp()}"
            test_data = f"Health check at {datetime.utcnow().isoformat()}"
            
            # 存储测试数据
            await self.store(test_key, test_data)
            
            # 检索测试数据
            retrieved = await self.retrieve(test_key)
            
            # 删除测试数据
            await self.delete(test_key)
            
            # 验证测试结果
            if retrieved and retrieved.get("data") == test_data.encode("utf-8"):
                return {
                    "status": "healthy",
                    "message": "S3存储后端运行正常",
                    "backend_type": "s3",
                    "endpoint": self.endpoint,
                    "bucket": self.bucket_name
                }
            else:
                return {
                    "status": "warning",
                    "message": "S3存储后端读写测试异常",
                    "backend_type": "s3",
                    "endpoint": self.endpoint,
                    "bucket": self.bucket_name
                }
        except Exception as e:
            logger.error(f"S3健康检查失败: {str(e)}")
            return {
                "status": "unhealthy",
                "message": f"S3存储后端异常: {str(e)}",
                "backend_type": "s3",
                "endpoint": self.endpoint,
                "bucket": self.bucket_name
            } 