from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
import time
from typing import Optional, List

from ..models.task_execution import TaskExecution
from ..schemas.task_execution import TaskExecutionCreate, TaskExecutionUpdate


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
        return execution

    async def get_execution(self, execution_id: str) -> Optional[TaskExecution]:
        """获取任务执行记录"""
        query = select(TaskExecution).where(TaskExecution.id == execution_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_executions_by_task(self, task_id: str) -> List[TaskExecution]:
        """获取任务的所有执行记录"""
        query = select(TaskExecution).where(TaskExecution.task_id == task_id).order_by(TaskExecution.started_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def complete_execution(self, execution_id: str, status: str, error_message: Optional[str] = None) -> Optional[TaskExecution]:
        """完成任务执行记录"""
        now = datetime.now()
        update_data = TaskExecutionUpdate(
            status=status,
            completed_at=now,
            error_message=error_message
        )
        return await self.update_execution(execution_id, update_data) 