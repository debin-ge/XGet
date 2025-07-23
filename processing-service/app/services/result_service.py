import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from ..models.processing_result import ProcessingResult
from ..models.processing_task import ProcessingTask
from ..schemas.processing_result import ProcessingResultCreate, ProcessingResultUpdate

logger = logging.getLogger(__name__)

class ResultService:
    """处理结果服务"""
    
    async def create_result(
        self, db: AsyncSession, result_data: ProcessingResultCreate
    ) -> ProcessingResult:
        """创建处理结果"""
        result_id = str(uuid.uuid4())
        result = ProcessingResult(
            id=result_id,
            task_id=result_data.task_id,
            data=result_data.data,
            metadata=result_data.metadata,
            storage_location=result_data.storage_location,
        )
        db.add(result)
        
        # 更新任务状态和结果ID
        task_query = select(ProcessingTask).where(ProcessingTask.id == result_data.task_id)
        task_result = await db.execute(task_query)
        task = task_result.scalar_one_or_none()
        if task:
            task.result_id = result_id
            task.status = "completed"
            task.progress = 100.0
            task.completed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(result)
        logger.info(f"创建处理结果: {result_id} 对应任务: {result_data.task_id}")
        return result
    
    async def get_result(self, db: AsyncSession, result_id: str) -> Optional[ProcessingResult]:
        """获取指定ID的处理结果"""
        query = select(ProcessingResult).where(ProcessingResult.id == result_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_result_with_task(self, db: AsyncSession, result_id: str) -> Optional[ProcessingResult]:
        """获取指定ID的处理结果，包括关联的任务信息"""
        query = select(ProcessingResult).options(
            joinedload(ProcessingResult.task)
        ).where(ProcessingResult.id == result_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_results(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        task_id: Optional[str] = None,
    ) -> Tuple[List[ProcessingResult], int]:
        """获取处理结果列表"""
        # 构建查询
        query = select(ProcessingResult)
        count_query = select(func.count()).select_from(ProcessingResult)
        
        # 应用过滤条件
        if task_id:
            query = query.where(ProcessingResult.task_id == task_id)
            count_query = count_query.where(ProcessingResult.task_id == task_id)
        
        # 应用排序和分页
        query = query.order_by(desc(ProcessingResult.created_at)).offset(skip).limit(limit)
        
        # 执行查询
        result = await db.execute(query)
        count_result = await db.execute(count_query)
        
        return result.scalars().all(), count_result.scalar_one()
    
    async def update_result(
        self, db: AsyncSession, result_id: str, result_data: ProcessingResultUpdate
    ) -> Optional[ProcessingResult]:
        """更新处理结果信息（仅限元数据和存储位置）"""
        # 获取现有结果
        result = await self.get_result(db, result_id)
        if not result:
            return None
        
        # 更新结果数据
        update_data = result_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(result, key, value)
        
        await db.commit()
        await db.refresh(result)
        logger.info(f"更新处理结果: {result_id}")
        return result
    
    async def delete_result(self, db: AsyncSession, result_id: str) -> bool:
        """删除处理结果（仅限管理操作）"""
        result = await self.get_result(db, result_id)
        if not result:
            return False
        
        # 更新关联的任务
        task_query = select(ProcessingTask).where(ProcessingTask.result_id == result_id)
        task_result = await db.execute(task_query)
        task = task_result.scalar_one_or_none()
        if task:
            task.result_id = None
        
        await db.delete(result)
        await db.commit()
        logger.info(f"删除处理结果: {result_id}")
        return True
    
    async def get_stats(
        self, db: AsyncSession, period: str = "daily", date: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取处理统计信息"""
        # 根据不同的时间周期聚合数据
        # 这里是一个简化的实现，实际应用中可能需要更复杂的SQL查询
        
        stats = {
            "period": period,
            "date": date or datetime.utcnow().strftime("%Y-%m-%d"),
            "total_results": 0,
            "by_task_type": {},
            "storage_usage": {}
        }
        
        # 获取总结果数
        count_query = select(func.count()).select_from(ProcessingResult)
        count_result = await db.execute(count_query)
        stats["total_results"] = count_result.scalar_one()
        
        # 按任务类型统计
        # 需要联合查询ProcessingTask表
        # 这里简化处理，实际应用中可能需要更复杂的SQL
        
        return stats 