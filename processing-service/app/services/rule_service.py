import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import select, update, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.processing_rule import ProcessingRule
from ..schemas.processing_rule import ProcessingRuleCreate, ProcessingRuleUpdate

logger = logging.getLogger(__name__)

class RuleService:
    """处理规则服务"""
    
    async def create_rule(self, db: AsyncSession, rule_data: ProcessingRuleCreate) -> ProcessingRule:
        """创建新的处理规则"""
        rule_id = str(uuid.uuid4())
        rule = ProcessingRule(
            id=rule_id,
            name=rule_data.name,
            description=rule_data.description,
            task_type=rule_data.task_type,
            rule_definition=rule_data.rule_definition,
            is_active=rule_data.is_active,
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        logger.info(f"创建处理规则: {rule_id}, 名称: {rule_data.name}")
        return rule
    
    async def get_rule(self, db: AsyncSession, rule_id: str) -> Optional[ProcessingRule]:
        """获取指定ID的处理规则"""
        query = select(ProcessingRule).where(ProcessingRule.id == rule_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_rules(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        task_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[ProcessingRule], int]:
        """获取处理规则列表"""
        # 构建查询
        query = select(ProcessingRule)
        count_query = select(func.count()).select_from(ProcessingRule)
        
        # 应用过滤条件
        if task_type:
            query = query.where(ProcessingRule.task_type == task_type)
            count_query = count_query.where(ProcessingRule.task_type == task_type)
        if is_active is not None:
            query = query.where(ProcessingRule.is_active == is_active)
            count_query = count_query.where(ProcessingRule.is_active == is_active)
        
        # 应用排序和分页
        query = query.order_by(desc(ProcessingRule.updated_at)).offset(skip).limit(limit)
        
        # 执行查询
        result = await db.execute(query)
        count_result = await db.execute(count_query)
        
        return result.scalars().all(), count_result.scalar_one()
    
    async def update_rule(
        self, db: AsyncSession, rule_id: str, rule_data: ProcessingRuleUpdate
    ) -> Optional[ProcessingRule]:
        """更新处理规则"""
        # 获取现有规则
        rule = await self.get_rule(db, rule_id)
        if not rule:
            return None
        
        # 更新规则数据
        update_data = rule_data.dict(exclude_unset=True)
        
        # 如果规则定义发生变化，增加版本号
        if "rule_definition" in update_data and update_data["rule_definition"] != rule.rule_definition:
            rule.version += 1
        
        # 应用更新
        for key, value in update_data.items():
            setattr(rule, key, value)
        
        await db.commit()
        await db.refresh(rule)
        logger.info(f"更新处理规则: {rule_id}, 版本: {rule.version}")
        return rule
    
    async def delete_rule(self, db: AsyncSession, rule_id: str) -> bool:
        """删除处理规则"""
        rule = await self.get_rule(db, rule_id)
        if not rule:
            return False
        
        await db.delete(rule)
        await db.commit()
        logger.info(f"删除处理规则: {rule_id}")
        return True
    
    async def get_rules_by_task_type(self, db: AsyncSession, task_type: str) -> List[ProcessingRule]:
        """获取指定任务类型的活跃处理规则"""
        query = select(ProcessingRule).where(
            ProcessingRule.task_type == task_type,
            ProcessingRule.is_active == True
        ).order_by(ProcessingRule.version.desc())
        
        result = await db.execute(query)
        return result.scalars().all() 