from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime
import time
from typing import Optional, List

from ..models.task_execution import TaskExecution
from ..schemas.task_execution import TaskExecutionCreate, TaskExecutionUpdate, TaskExecutionListResponse
from ..core.cache import cache
from ..core.redis import RedisManager
from ..core.logging import logger


class TaskExecutionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_execution(self, execution_data: TaskExecutionCreate) -> TaskExecution:
        """创建任务执行记录"""
        execution = TaskExecution(
            task_id=execution_data.task_id,
            account_id=execution_data.account_id,
            proxy_id=execution_data.proxy_id,
            status=execution_data.status,
            started_at=execution_data.started_at
        )
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)
        return execution

    async def update_execution(self, execution_id: str, execution_data: TaskExecutionUpdate) -> Optional[TaskExecution]:
        """更新任务执行记录"""
        query = select(TaskExecution).where(TaskExecution.id == execution_id)
        result = await self.db.execute(query)
        execution = result.scalars().first()
        
        if not execution:
            return None
            
        if execution_data.status:
            execution.status = execution_data.status
            
        if execution_data.completed_at:
            execution.completed_at = execution_data.completed_at
            
        if execution_data.duration:
            execution.duration = execution_data.duration
        elif execution_data.completed_at and execution.started_at:
            # 自动计算执行时长（秒）
            duration = (execution_data.completed_at - execution.started_at).total_seconds()
            execution.duration = int(duration)
            
        if execution_data.error_message:
            execution.error_message = execution_data.error_message 
            
        await self.db.commit()
        await self.db.refresh(execution)
        
        # 清除相关缓存
        await self.invalidate_execution_cache(execution_id)
        if execution.task_id:
            await self.invalidate_task_executions_cache(execution.task_id)
        
        return execution

    @cache(prefix="execution", expire=120)  # 2分钟缓存
    async def get_execution(self, execution_id: str) -> Optional[TaskExecution]:
        """获取任务执行记录"""
        query = select(TaskExecution).where(TaskExecution.id == execution_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    @cache(prefix="executions_by_task", expire=120)  # 2分钟缓存
    async def get_executions_by_task(self, task_id: str) -> List[TaskExecution]:
        """获取任务的所有执行记录"""
        query = select(TaskExecution).where(TaskExecution.task_id == task_id).order_by(TaskExecution.started_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    @cache(prefix="executions_by_task_paginated", expire=120)  # 2分钟缓存
    async def get_executions_by_task_paginated(
        self,
        task_id: str,
        page: int = 1,
        size: int = 20
    ) -> TaskExecutionListResponse:
        """获取任务执行记录的分页列表"""
        # 构建查询条件
        query = select(TaskExecution).where(TaskExecution.task_id == task_id).order_by(TaskExecution.started_at.desc())
        count_query = select(func.count(TaskExecution.id)).where(TaskExecution.task_id == task_id)
        
        # 获取总数
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 获取分页数据
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)
        result = await self.db.execute(query)
        executions = result.scalars().all()
        
        return TaskExecutionListResponse.create(executions, total, page, size)

    async def complete_execution(self, execution_id: str, status: str, error_message: Optional[str] = None) -> Optional[TaskExecution]:
        """完成任务执行记录"""
        now = datetime.now()
        update_data = TaskExecutionUpdate(
            status=status,
            completed_at=now,
            error_message=error_message
        )
        
        # 更新执行记录并清除缓存
        result = await self.update_execution(execution_id, update_data)
        
        # 如果执行完成，清除任务相关的缓存
        if result and status in ["COMPLETED", "FAILED"]:
            task_execution = await self.get_execution(execution_id)
            if task_execution and task_execution.task_id:
                # 清除任务相关的缓存，因为任务状态可能已改变
                await self.invalidate_task_executions_cache(task_execution.task_id)
                # 清除任务列表缓存
                await RedisManager.delete_keys(f"tasks:*")
                await RedisManager.delete_keys(f"tasks_paginated:*")
        
        return result

    async def invalidate_execution_cache(self, execution_id: str):
        """清除任务执行相关的缓存"""
        try:
            # 清除单个执行记录缓存
            await RedisManager.delete_keys(f"execution:{execution_id}*")
            await RedisManager.delete_keys(f"execution:{execution_id}:*")
            # 清除执行记录列表缓存
            await RedisManager.delete_keys(f"executions_by_task:*")
            await RedisManager.delete_keys(f"executions_by_task_paginated:*")
            logger.info(f"Cleared cache for execution {execution_id}")
        except Exception as e:
            logger.warning(f"Failed to clear execution cache for {execution_id}: {e}")

    async def invalidate_task_executions_cache(self, task_id: str):
        """清除任务所有执行记录的缓存"""
        try:
            await RedisManager.delete_keys(f"executions_by_task:{task_id}*")
            await RedisManager.delete_keys(f"executions_by_task_paginated:{task_id}*")
            logger.info(f"Cleared cache for all executions of task {task_id}")
        except Exception as e:
            logger.warning(f"Failed to clear executions cache for task {task_id}: {e}")
