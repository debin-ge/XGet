import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import select, update, delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.storage_backend import StorageBackend
from ..schemas.storage_backend import StorageBackendCreate, StorageBackendUpdate
from ..storage.factory import StorageBackendFactory

logger = logging.getLogger(__name__)

class BackendService:
    """存储后端管理服务"""
    
    async def create_backend(
        self, db: AsyncSession, backend_data: StorageBackendCreate
    ) -> Optional[StorageBackend]:
        """
        创建存储后端
        
        Args:
            db: 数据库会话
            backend_data: 存储后端数据
            
        Returns:
            创建的存储后端
        """
        try:
            # 检查名称是否已存在
            query = select(StorageBackend).where(StorageBackend.name == backend_data.name)
            result = await db.execute(query)
            existing = result.scalar_one_or_none()
            if existing:
                logger.warning(f"存储后端名称已存在: {backend_data.name}")
                return None
            
            # 创建后端记录
            backend_id = str(uuid.uuid4())
            backend = StorageBackend(
                id=backend_id,
                name=backend_data.name,
                type=backend_data.type,
                configuration=backend_data.configuration,
                status=backend_data.status,
                priority=backend_data.priority,
                capacity=backend_data.capacity,
                used_space=backend_data.used_space or 0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(backend)
            
            # 测试后端连接
            test_backend = await StorageBackendFactory.create_backend(
                backend_data.type, backend_data.configuration
            )
            if not test_backend:
                logger.error(f"存储后端连接测试失败: {backend_data.name}")
                await db.rollback()
                return None
            
            # 如果连接测试成功，提交事务
            await db.commit()
            await db.refresh(backend)
            
            # 清除工厂缓存，以便下次使用时重新创建
            StorageBackendFactory.clear_cache()
            
            logger.info(f"创建存储后端: {backend_id}, {backend_data.name}")
            return backend
        except Exception as e:
            await db.rollback()
            logger.error(f"创建存储后端失败: {str(e)}")
            return None
    
    async def get_backend(self, db: AsyncSession, backend_id: str) -> Optional[StorageBackend]:
        """
        获取存储后端
        
        Args:
            db: 数据库会话
            backend_id: 存储后端ID
            
        Returns:
            存储后端
        """
        query = select(StorageBackend).where(StorageBackend.id == backend_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_backend_by_name(self, db: AsyncSession, name: str) -> Optional[StorageBackend]:
        """
        通过名称获取存储后端
        
        Args:
            db: 数据库会话
            name: 存储后端名称
            
        Returns:
            存储后端
        """
        query = select(StorageBackend).where(StorageBackend.name == name)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_backends(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        type: Optional[str] = None
    ) -> Tuple[List[StorageBackend], int]:
        """
        获取存储后端列表
        
        Args:
            db: 数据库会话
            skip: 跳过数量
            limit: 限制数量
            status: 状态过滤
            type: 类型过滤
            
        Returns:
            存储后端列表和总数
        """
        # 构建查询
        query = select(StorageBackend)
        count_query = select(func.count()).select_from(StorageBackend)
        
        # 应用过滤条件
        filters = []
        if status:
            filters.append(StorageBackend.status == status)
        if type:
            filters.append(StorageBackend.type == type)
        
        if filters:
            query = query.where(*filters)
            count_query = count_query.where(*filters)
        
        # 应用排序和分页
        query = query.order_by(desc(StorageBackend.priority)).offset(skip).limit(limit)
        
        # 执行查询
        result = await db.execute(query)
        count_result = await db.execute(count_query)
        
        return result.scalars().all(), count_result.scalar_one()
    
    async def update_backend(
        self, db: AsyncSession, backend_id: str, backend_data: StorageBackendUpdate
    ) -> Optional[StorageBackend]:
        """
        更新存储后端
        
        Args:
            db: 数据库会话
            backend_id: 存储后端ID
            backend_data: 更新数据
            
        Returns:
            更新后的存储后端
        """
        # 获取现有后端
        backend = await self.get_backend(db, backend_id)
        if not backend:
            return None
        
        try:
            # 如果更新了名称，检查是否已存在
            if backend_data.name and backend_data.name != backend.name:
                query = select(StorageBackend).where(StorageBackend.name == backend_data.name)
                result = await db.execute(query)
                existing = result.scalar_one_or_none()
                if existing:
                    logger.warning(f"存储后端名称已存在: {backend_data.name}")
                    return None
            
            # 更新字段
            update_data = backend_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(backend, key, value)
            
            backend.updated_at = datetime.utcnow()
            
            # 如果更新了配置或类型，测试连接
            if "configuration" in update_data or "type" in update_data:
                test_backend = await StorageBackendFactory.create_backend(
                    backend.type, backend.configuration
                )
                if not test_backend:
                    logger.error(f"存储后端连接测试失败: {backend.name}")
                    await db.rollback()
                    return None
                
                # 清除工厂缓存
                StorageBackendFactory.clear_cache()
            
            await db.commit()
            await db.refresh(backend)
            
            logger.info(f"更新存储后端: {backend_id}, {backend.name}")
            return backend
        except Exception as e:
            await db.rollback()
            logger.error(f"更新存储后端失败: {str(e)}")
            return None
    
    async def delete_backend(self, db: AsyncSession, backend_id: str) -> bool:
        """
        删除存储后端
        
        Args:
            db: 数据库会话
            backend_id: 存储后端ID
            
        Returns:
            删除是否成功
        """
        # 获取后端
        backend = await self.get_backend(db, backend_id)
        if not backend:
            return False
        
        try:
            # 检查是否有存储项使用此后端
            from ..models.storage_item import StorageItem
            query = select(func.count()).select_from(StorageItem).where(
                StorageItem.storage_backend == backend.name
            )
            result = await db.execute(query)
            count = result.scalar_one()
            
            if count > 0:
                logger.warning(f"无法删除存储后端，有 {count} 个存储项正在使用: {backend.name}")
                return False
            
            # 删除后端
            await db.delete(backend)
            await db.commit()
            
            # 清除工厂缓存
            StorageBackendFactory.clear_cache()
            
            logger.info(f"删除存储后端: {backend_id}, {backend.name}")
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"删除存储后端失败: {str(e)}")
            return False
    
    async def test_backend(self, db: AsyncSession, backend_id: str) -> Dict[str, Any]:
        """
        测试存储后端连接
        
        Args:
            db: 数据库会话
            backend_id: 存储后端ID
            
        Returns:
            测试结果
        """
        # 获取后端
        backend = await self.get_backend(db, backend_id)
        if not backend:
            return {
                "success": False,
                "message": f"存储后端不存在: {backend_id}"
            }
        
        try:
            # 创建后端实例
            backend_instance = await StorageBackendFactory.get_backend(backend_id, backend)
            if not backend_instance:
                return {
                    "success": False,
                    "message": f"无法创建存储后端实例: {backend.name}"
                }
            
            # 执行健康检查
            health = await backend_instance.health_check()
            
            return {
                "success": health.get("status") == "healthy",
                "message": health.get("message", ""),
                "details": health
            }
        except Exception as e:
            logger.error(f"测试存储后端失败: {str(e)}")
            return {
                "success": False,
                "message": f"测试失败: {str(e)}",
                "error": str(e)
            } 