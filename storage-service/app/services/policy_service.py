import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import select, update, delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.retention_policy import RetentionPolicy
from ..schemas.retention_policy import RetentionPolicyCreate, RetentionPolicyUpdate

logger = logging.getLogger(__name__)

class PolicyService:
    """保留策略管理服务"""
    
    async def create_policy(
        self, db: AsyncSession, policy_data: RetentionPolicyCreate
    ) -> Optional[RetentionPolicy]:
        """
        创建保留策略
        
        Args:
            db: 数据库会话
            policy_data: 保留策略数据
            
        Returns:
            创建的保留策略
        """
        try:
            # 检查名称是否已存在
            query = select(RetentionPolicy).where(RetentionPolicy.name == policy_data.name)
            result = await db.execute(query)
            existing = result.scalar_one_or_none()
            if existing:
                logger.warning(f"保留策略名称已存在: {policy_data.name}")
                return None
            
            # 验证时间周期
            if policy_data.active_period < 0:
                logger.warning("活跃期不能为负数")
                return None
            
            if policy_data.archive_period < 0:
                logger.warning("归档期不能为负数")
                return None
            
            if policy_data.total_retention < policy_data.active_period:
                logger.warning("总保留期必须大于或等于活跃期")
                return None
            
            # 创建策略记录
            policy_id = str(uuid.uuid4())
            policy = RetentionPolicy(
                id=policy_id,
                name=policy_data.name,
                description=policy_data.description,
                active_period=policy_data.active_period,
                archive_period=policy_data.archive_period,
                total_retention=policy_data.total_retention,
                auto_delete=policy_data.auto_delete,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(policy)
            await db.commit()
            await db.refresh(policy)
            
            logger.info(f"创建保留策略: {policy_id}, {policy_data.name}")
            return policy
        except Exception as e:
            await db.rollback()
            logger.error(f"创建保留策略失败: {str(e)}")
            return None
    
    async def get_policy(self, db: AsyncSession, policy_id: str) -> Optional[RetentionPolicy]:
        """
        获取保留策略
        
        Args:
            db: 数据库会话
            policy_id: 保留策略ID
            
        Returns:
            保留策略
        """
        query = select(RetentionPolicy).where(RetentionPolicy.id == policy_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_policy_by_name(self, db: AsyncSession, name: str) -> Optional[RetentionPolicy]:
        """
        通过名称获取保留策略
        
        Args:
            db: 数据库会话
            name: 保留策略名称
            
        Returns:
            保留策略
        """
        query = select(RetentionPolicy).where(RetentionPolicy.name == name)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_policies(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[RetentionPolicy], int]:
        """
        获取保留策略列表
        
        Args:
            db: 数据库会话
            skip: 跳过数量
            limit: 限制数量
            
        Returns:
            保留策略列表和总数
        """
        # 构建查询
        query = select(RetentionPolicy)
        count_query = select(func.count()).select_from(RetentionPolicy)
        
        # 应用排序和分页
        query = query.order_by(RetentionPolicy.name).offset(skip).limit(limit)
        
        # 执行查询
        result = await db.execute(query)
        count_result = await db.execute(count_query)
        
        return result.scalars().all(), count_result.scalar_one()
    
    async def update_policy(
        self, db: AsyncSession, policy_id: str, policy_data: RetentionPolicyUpdate
    ) -> Optional[RetentionPolicy]:
        """
        更新保留策略
        
        Args:
            db: 数据库会话
            policy_id: 保留策略ID
            policy_data: 更新数据
            
        Returns:
            更新后的保留策略
        """
        # 获取现有策略
        policy = await self.get_policy(db, policy_id)
        if not policy:
            return None
        
        try:
            # 如果更新了名称，检查是否已存在
            if policy_data.name and policy_data.name != policy.name:
                query = select(RetentionPolicy).where(RetentionPolicy.name == policy_data.name)
                result = await db.execute(query)
                existing = result.scalar_one_or_none()
                if existing:
                    logger.warning(f"保留策略名称已存在: {policy_data.name}")
                    return None
            
            # 验证时间周期
            update_data = policy_data.dict(exclude_unset=True)
            
            active_period = update_data.get("active_period", policy.active_period)
            archive_period = update_data.get("archive_period", policy.archive_period)
            total_retention = update_data.get("total_retention", policy.total_retention)
            
            if active_period < 0:
                logger.warning("活跃期不能为负数")
                return None
            
            if archive_period < 0:
                logger.warning("归档期不能为负数")
                return None
            
            if total_retention < active_period:
                logger.warning("总保留期必须大于或等于活跃期")
                return None
            
            # 更新字段
            for key, value in update_data.items():
                setattr(policy, key, value)
            
            policy.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(policy)
            
            logger.info(f"更新保留策略: {policy_id}, {policy.name}")
            return policy
        except Exception as e:
            await db.rollback()
            logger.error(f"更新保留策略失败: {str(e)}")
            return None
    
    async def delete_policy(self, db: AsyncSession, policy_id: str) -> bool:
        """
        删除保留策略
        
        Args:
            db: 数据库会话
            policy_id: 保留策略ID
            
        Returns:
            删除是否成功
        """
        # 获取策略
        policy = await self.get_policy(db, policy_id)
        if not policy:
            return False
        
        try:
            # 检查是否有元数据使用此策略
            from ..models.metadata import Metadata
            query = select(func.count()).select_from(Metadata).where(
                Metadata.retention_policy == policy.name
            )
            result = await db.execute(query)
            count = result.scalar_one()
            
            if count > 0:
                logger.warning(f"无法删除保留策略，有 {count} 个存储项正在使用: {policy.name}")
                return False
            
            # 删除策略
            await db.delete(policy)
            await db.commit()
            
            logger.info(f"删除保留策略: {policy_id}, {policy.name}")
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"删除保留策略失败: {str(e)}")
            return False 