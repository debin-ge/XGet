import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from sqlalchemy import select, update, delete, desc, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..models.storage_item import StorageItem
from ..models.metadata import Metadata
from ..models.storage_backend import StorageBackend
from ..models.retention_policy import RetentionPolicy
from ..schemas.storage_item import StorageItemCreate, StorageItemUpdate
from ..schemas.metadata import MetadataCreate, MetadataUpdate
from ..schemas.storage import StorageRequest, BatchStorageRequest, StorageOptions
from ..storage.factory import StorageBackendFactory
from ..core.config import settings
from ..db.database import mongo_db

logger = logging.getLogger(__name__)

class StorageService:
    """存储服务"""
    
    async def store_data(
        self, 
        db: AsyncSession, 
        storage_request: StorageRequest,
        default_backend: str = "S3"
    ) -> Dict[str, Any]:
        """
        存储数据
        
        Args:
            db: 数据库会话
            storage_request: 存储请求
            default_backend: 默认存储后端类型
            
        Returns:
            存储结果
        """
        try:
            # 生成唯一ID
            item_id = str(uuid.uuid4())
            
            # 获取存储选项
            options = storage_request.storage_options or StorageOptions()
            
            # 选择存储后端
            backend = await StorageBackendFactory.get_backend(default_backend)
            if not backend:
                raise ValueError(f"无法创建存储后端: {default_backend}")
            
            # 构建存储键
            key = f"{storage_request.data_type}/{item_id}"
            
            # 存储数据
            storage_result = await backend.store(
                key, 
                storage_request.content,
                storage_request.metadata
            )
            
            # 创建存储项记录
            storage_item = StorageItem(
                id=item_id,
                data_type=storage_request.data_type,
                content_hash=storage_result.get("content_hash", ""),
                size=storage_result.get("size", 0),
                storage_location=storage_result.get("storage_location", ""),
                storage_backend=default_backend,
                compression=options.compression,
                encryption=options.encryption,
                version=1,
                status="stored",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(storage_item)
            
            # 创建元数据记录
            if storage_request.metadata:
                # 提取标签和自定义字段
                tags = storage_request.metadata.get("tags", [])
                custom_fields = {k: v for k, v in storage_request.metadata.items() if k != "tags"}
                
                # 获取源ID和处理ID
                source_id = storage_request.metadata.get("source_id")
                processing_id = storage_request.metadata.get("processing_id")
                
                # 获取保留策略
                retention_policy = storage_request.metadata.get("retention_policy", "standard")
                
                metadata = Metadata(
                    item_id=item_id,
                    source_id=source_id,
                    processing_id=processing_id,
                    tags=tags,
                    custom_fields=custom_fields,
                    retention_policy=retention_policy,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(metadata)
            
            await db.commit()
            
            # 返回结果
            return {
                "id": item_id,
                "data_type": storage_request.data_type,
                "size": storage_result.get("size", 0),
                "storage_location": storage_result.get("storage_location", ""),
                "storage_backend": default_backend,
                "metadata": storage_request.metadata,
                "created_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            await db.rollback()
            logger.error(f"存储数据失败: {str(e)}")
            
            # 如果数据库操作失败但存储成功，尝试备份到MongoDB
            if 'storage_result' in locals() and mongo_db:
                try:
                    collection = mongo_db.backup_data
                    backup_data = {
                        "id": item_id,
                        "data_type": storage_request.data_type,
                        "content": storage_request.content,
                        "metadata": storage_request.metadata,
                        "storage_result": storage_result,
                        "backup_timestamp": datetime.utcnow().isoformat()
                    }
                    await collection.insert_one(backup_data)
                    logger.info(f"数据已备份到MongoDB: {item_id}")
                except Exception as mongo_err:
                    logger.error(f"MongoDB备份失败: {str(mongo_err)}")
            
            raise
    
    async def store_batch(
        self, 
        db: AsyncSession, 
        batch_request: BatchStorageRequest,
        default_backend: str = "S3"
    ) -> List[Dict[str, Any]]:
        """
        批量存储数据
        
        Args:
            db: 数据库会话
            batch_request: 批量存储请求
            default_backend: 默认存储后端类型
            
        Returns:
            存储结果列表
        """
        results = []
        for item in batch_request.items:
            try:
                result = await self.store_data(db, item, default_backend)
                results.append(result)
            except Exception as e:
                logger.error(f"批量存储项失败: {str(e)}")
                results.append({"error": str(e), "status": "failed"})
        
        return results
    
    async def get_item(
        self, 
        db: AsyncSession, 
        item_id: str,
        include_data: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        获取存储项
        
        Args:
            db: 数据库会话
            item_id: 存储项ID
            include_data: 是否包含数据内容
            
        Returns:
            存储项信息
        """
        # 查询存储项和元数据
        query = select(StorageItem).options(
            selectinload(StorageItem.metadata)
        ).where(StorageItem.id == item_id)
        
        result = await db.execute(query)
        item = result.scalar_one_or_none()
        
        if not item:
            return None
        
        # 更新访问时间和计数
        item.accessed_at = datetime.utcnow()
        if item.metadata:
            item.metadata.access_count += 1
            item.metadata.last_accessed = datetime.utcnow()
        
        await db.commit()
        
        # 构建响应
        response = {
            "id": item.id,
            "data_type": item.data_type,
            "size": item.size,
            "storage_location": item.storage_location,
            "storage_backend": item.storage_backend,
            "compression": item.compression,
            "encryption": item.encryption,
            "version": item.version,
            "status": item.status,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "accessed_at": item.accessed_at,
            "metadata": None
        }
        
        # 添加元数据
        if item.metadata:
            response["metadata"] = {
                "source_id": item.metadata.source_id,
                "processing_id": item.metadata.processing_id,
                "tags": item.metadata.tags,
                "custom_fields": item.metadata.custom_fields,
                "retention_policy": item.metadata.retention_policy,
                "access_count": item.metadata.access_count,
                "last_accessed": item.metadata.last_accessed
            }
        
        # 如果需要，获取数据内容
        if include_data:
            backend = await StorageBackendFactory.get_backend(item.storage_backend)
            if backend:
                key = f"{item.data_type}/{item.id}"
                data_result = await backend.retrieve(key)
                if data_result:
                    response["data"] = data_result.get("data")
        
        return response
    
    async def search_items(
        self,
        db: AsyncSession,
        query: str = None,
        data_type: str = None,
        tags: List[str] = None,
        source_id: str = None,
        processing_id: str = None,
        status: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        搜索存储项
        
        Args:
            db: 数据库会话
            query: 搜索查询
            data_type: 数据类型
            tags: 标签列表
            source_id: 源ID
            processing_id: 处理ID
            status: 状态
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制数量
            offset: 偏移量
            sort_by: 排序字段
            sort_order: 排序顺序
            
        Returns:
            存储项列表和总数
        """
        # 构建查询
        query_obj = select(StorageItem).options(
            selectinload(StorageItem.metadata)
        )
        
        # 应用过滤条件
        filters = []
        
        if data_type:
            filters.append(StorageItem.data_type == data_type)
        
        if status:
            filters.append(StorageItem.status == status)
        
        if start_date:
            filters.append(StorageItem.created_at >= start_date)
        
        if end_date:
            filters.append(StorageItem.created_at <= end_date)
        
        # 元数据过滤
        metadata_filters = []
        
        if source_id:
            metadata_filters.append(Metadata.source_id == source_id)
        
        if processing_id:
            metadata_filters.append(Metadata.processing_id == processing_id)
        
        if tags:
            # 这里假设tags存储为JSON数组
            for tag in tags:
                metadata_filters.append(Metadata.tags.contains([tag]))
        
        # 如果有元数据过滤，添加连接条件
        if metadata_filters:
            query_obj = query_obj.join(Metadata, StorageItem.id == Metadata.item_id)
            filters.extend(metadata_filters)
        
        # 应用所有过滤条件
        if filters:
            query_obj = query_obj.where(and_(*filters))
        
        # 应用排序
        if sort_by == "created_at":
            if sort_order.lower() == "desc":
                query_obj = query_obj.order_by(desc(StorageItem.created_at))
            else:
                query_obj = query_obj.order_by(StorageItem.created_at)
        elif sort_by == "updated_at":
            if sort_order.lower() == "desc":
                query_obj = query_obj.order_by(desc(StorageItem.updated_at))
            else:
                query_obj = query_obj.order_by(StorageItem.updated_at)
        elif sort_by == "size":
            if sort_order.lower() == "desc":
                query_obj = query_obj.order_by(desc(StorageItem.size))
            else:
                query_obj = query_obj.order_by(StorageItem.size)
        
        # 计算总数
        count_query = select(func.count()).select_from(query_obj.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()
        
        # 应用分页
        query_obj = query_obj.offset(offset).limit(limit)
        
        # 执行查询
        result = await db.execute(query_obj)
        items = result.scalars().all()
        
        # 构建响应
        response_items = []
        for item in items:
            item_dict = {
                "id": item.id,
                "data_type": item.data_type,
                "size": item.size,
                "storage_location": item.storage_location,
                "storage_backend": item.storage_backend,
                "status": item.status,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
                "metadata": None
            }
            
            # 添加元数据
            if item.metadata:
                item_dict["metadata"] = {
                    "source_id": item.metadata.source_id,
                    "processing_id": item.metadata.processing_id,
                    "tags": item.metadata.tags,
                    "retention_policy": item.metadata.retention_policy,
                    "access_count": item.metadata.access_count,
                    "last_accessed": item.metadata.last_accessed
                }
            
            response_items.append(item_dict)
        
        return response_items, total
    
    async def update_item(
        self,
        db: AsyncSession,
        item_id: str,
        item_update: StorageItemUpdate,
        metadata_update: Optional[MetadataUpdate] = None
    ) -> Optional[Dict[str, Any]]:
        """
        更新存储项
        
        Args:
            db: 数据库会话
            item_id: 存储项ID
            item_update: 存储项更新数据
            metadata_update: 元数据更新数据
            
        Returns:
            更新后的存储项信息
        """
        # 查询存储项
        query = select(StorageItem).options(
            selectinload(StorageItem.metadata)
        ).where(StorageItem.id == item_id)
        
        result = await db.execute(query)
        item = result.scalar_one_or_none()
        
        if not item:
            return None
        
        # 更新存储项
        update_data = item_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)
        
        item.updated_at = datetime.utcnow()
        
        # 更新元数据
        if metadata_update and item.metadata:
            metadata_data = metadata_update.dict(exclude_unset=True)
            for key, value in metadata_data.items():
                setattr(item.metadata, key, value)
            
            item.metadata.updated_at = datetime.utcnow()
        
        await db.commit()
        
        # 返回更新后的项
        return await self.get_item(db, item_id)
    
    async def delete_item(self, db: AsyncSession, item_id: str) -> bool:
        """
        删除存储项
        
        Args:
            db: 数据库会话
            item_id: 存储项ID
            
        Returns:
            删除是否成功
        """
        # 查询存储项
        query = select(StorageItem).where(StorageItem.id == item_id)
        result = await db.execute(query)
        item = result.scalar_one_or_none()
        
        if not item:
            return False
        
        try:
            # 从存储后端删除数据
            backend = await StorageBackendFactory.get_backend(item.storage_backend)
            if backend:
                key = f"{item.data_type}/{item.id}"
                await backend.delete(key)
            
            # 删除元数据和存储项
            await db.delete(item)
            await db.commit()
            
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"删除存储项失败: {str(e)}")
            return False
    
    async def get_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Args:
            db: 数据库会话
            
        Returns:
            统计信息
        """
        try:
            # 获取总项数
            count_query = select(func.count()).select_from(StorageItem)
            count_result = await db.execute(count_query)
            total_items = count_result.scalar_one()
            
            # 获取总大小
            size_query = select(func.sum(StorageItem.size)).select_from(StorageItem)
            size_result = await db.execute(size_query)
            total_size = size_result.scalar_one() or 0
            
            # 按数据类型分组
            type_query = select(
                StorageItem.data_type,
                func.count().label("count"),
                func.sum(StorageItem.size).label("size")
            ).group_by(StorageItem.data_type)
            type_result = await db.execute(type_query)
            by_data_type = {
                row.data_type: {"count": row.count, "size": row.size or 0}
                for row in type_result
            }
            
            # 按存储后端分组
            backend_query = select(
                StorageItem.storage_backend,
                func.count().label("count"),
                func.sum(StorageItem.size).label("size")
            ).group_by(StorageItem.storage_backend)
            backend_result = await db.execute(backend_query)
            by_storage_backend = {
                row.storage_backend: {"count": row.count, "size": row.size or 0}
                for row in backend_result
            }
            
            # 按状态分组
            status_query = select(
                StorageItem.status,
                func.count().label("count")
            ).group_by(StorageItem.status)
            status_result = await db.execute(status_query)
            by_status = {row.status: row.count for row in status_result}
            
            return {
                "total_items": total_items,
                "total_size": total_size,
                "by_data_type": by_data_type,
                "by_storage_backend": by_storage_backend,
                "by_status": by_status,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"获取存储统计信息失败: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_lifecycle_info(self, db: AsyncSession, item_id: str) -> Optional[Dict[str, Any]]:
        """
        获取存储项生命周期信息
        
        Args:
            db: 数据库会话
            item_id: 存储项ID
            
        Returns:
            生命周期信息
        """
        # 查询存储项和元数据
        query = select(StorageItem).options(
            selectinload(StorageItem.metadata)
        ).where(StorageItem.id == item_id)
        
        result = await db.execute(query)
        item = result.scalar_one_or_none()
        
        if not item:
            return None
        
        # 获取保留策略
        retention_policy_name = None
        if item.metadata:
            retention_policy_name = item.metadata.retention_policy
        
        # 查询保留策略
        policy = None
        if retention_policy_name:
            policy_query = select(RetentionPolicy).where(
                RetentionPolicy.name == retention_policy_name
            )
            policy_result = await db.execute(policy_query)
            policy = policy_result.scalar_one_or_none()
        
        # 计算时间
        now = datetime.utcnow()
        days_since_creation = (now - item.created_at).days
        days_since_last_access = None
        if item.metadata and item.metadata.last_accessed:
            days_since_last_access = (now - item.metadata.last_accessed).days
        
        # 计算归档和删除时间
        days_until_archive = None
        days_until_deletion = None
        
        if policy:
            # 如果有策略，使用策略中的时间
            if item.status == "stored":
                days_until_archive = max(0, policy.active_period - days_since_creation)
            elif item.status == "archived":
                days_until_deletion = max(0, policy.total_retention - days_since_creation)
        
        # 构建响应
        return {
            "item_id": item.id,
            "lifecycle_info": {
                "retention_policy": retention_policy_name,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
                "accessed_at": item.accessed_at,
                "status": item.status,
                "days_since_creation": days_since_creation,
                "days_since_last_access": days_since_last_access,
                "days_until_archive": days_until_archive,
                "days_until_deletion": days_until_deletion
            }
        }
    
    async def update_lifecycle(
        self,
        db: AsyncSession,
        item_id: str,
        retention_policy: str
    ) -> Optional[Dict[str, Any]]:
        """
        更新存储项生命周期策略
        
        Args:
            db: 数据库会话
            item_id: 存储项ID
            retention_policy: 保留策略名称
            
        Returns:
            更新结果
        """
        # 查询存储项和元数据
        query = select(StorageItem).options(
            selectinload(StorageItem.metadata)
        ).where(StorageItem.id == item_id)
        
        result = await db.execute(query)
        item = result.scalar_one_or_none()
        
        if not item:
            return None
        
        # 查询保留策略
        policy_query = select(RetentionPolicy).where(
            RetentionPolicy.name == retention_policy
        )
        policy_result = await db.execute(policy_query)
        policy = policy_result.scalar_one_or_none()
        
        if not policy:
            return {
                "item_id": item_id,
                "applied": False,
                "message": f"保留策略不存在: {retention_policy}"
            }
        
        # 更新元数据
        if not item.metadata:
            # 如果没有元数据，创建一个
            metadata = Metadata(
                item_id=item_id,
                retention_policy=retention_policy,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(metadata)
        else:
            # 更新现有元数据
            item.metadata.retention_policy = retention_policy
            item.metadata.updated_at = datetime.utcnow()
        
        await db.commit()
        
        # 获取更新后的生命周期信息
        lifecycle_info = await self.get_lifecycle_info(db, item_id)
        
        return {
            "item_id": item_id,
            "lifecycle_info": lifecycle_info["lifecycle_info"],
            "applied": True,
            "message": f"已应用保留策略: {retention_policy}"
        }
    
    async def process_lifecycle_tasks(self, db: AsyncSession) -> Dict[str, Any]:
        """
        处理生命周期任务（归档和删除）
        
        Args:
            db: 数据库会话
            
        Returns:
            处理结果
        """
        try:
            # 获取所有保留策略
            policy_query = select(RetentionPolicy)
            policy_result = await db.execute(policy_query)
            policies = {p.name: p for p in policy_result.scalars().all()}
            
            # 处理结果统计
            results = {
                "archived": 0,
                "deleted": 0,
                "errors": 0
            }
            
            # 处理归档
            for policy_name, policy in policies.items():
                # 查找需要归档的项
                archive_date = datetime.utcnow() - timedelta(days=policy.active_period)
                
                # 查询符合归档条件的项
                archive_query = select(StorageItem).join(
                    Metadata, StorageItem.id == Metadata.item_id
                ).where(
                    and_(
                        StorageItem.status == "stored",
                        StorageItem.created_at <= archive_date,
                        Metadata.retention_policy == policy_name
                    )
                )
                
                archive_result = await db.execute(archive_query)
                archive_items = archive_result.scalars().all()
                
                # 归档项
                for item in archive_items:
                    try:
                        item.status = "archived"
                        item.updated_at = datetime.utcnow()
                        results["archived"] += 1
                    except Exception as e:
                        logger.error(f"归档项失败: {item.id}, {str(e)}")
                        results["errors"] += 1
            
            # 处理删除
            for policy_name, policy in policies.items():
                if policy.auto_delete:
                    # 查找需要删除的项
                    delete_date = datetime.utcnow() - timedelta(days=policy.total_retention)
                    
                    # 查询符合删除条件的项
                    delete_query = select(StorageItem).join(
                        Metadata, StorageItem.id == Metadata.item_id
                    ).where(
                        and_(
                            StorageItem.created_at <= delete_date,
                            Metadata.retention_policy == policy_name
                        )
                    )
                    
                    delete_result = await db.execute(delete_query)
                    delete_items = delete_result.scalars().all()
                    
                    # 删除项
                    for item in delete_items:
                        try:
                            success = await self.delete_item(db, item.id)
                            if success:
                                results["deleted"] += 1
                            else:
                                results["errors"] += 1
                        except Exception as e:
                            logger.error(f"删除项失败: {item.id}, {str(e)}")
                            results["errors"] += 1
            
            await db.commit()
            
            return {
                "status": "success",
                "results": results,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            await db.rollback()
            logger.error(f"处理生命周期任务失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            } 