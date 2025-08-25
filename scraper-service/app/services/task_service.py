from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, desc, func
from ..models.task import Task
from ..schemas.task import TaskCreate, TaskUpdate, TaskListResponse
import uuid
from datetime import datetime
from ..core.logging import logger
from .kafka_client import kafka_client

class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, task_data: TaskCreate) -> Task:
        """创建采集任务"""
        task = Task(
            id=str(uuid.uuid4()),
            task_name=task_data.task_name,
            describe=task_data.describe,
            task_type=task_data.task_type,
            parameters=task_data.parameters,
            account_id=task_data.account_id,
            proxy_id=task_data.proxy_id,
            user_id=task_data.user_id,
            status="PENDING"
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        
        # 发送任务到Kafka
        task_message = {
            "task_id": task.id,
            "task_name": task.task_name,
            "task_type": task.task_type,
            "parameters": task.parameters,
            "account_id": task.account_id,
            "proxy_id": task.proxy_id,
            "user_id": task.user_id,
            "created_at": datetime.now().isoformat()
        }
        
        success = await kafka_client.send_task(task_message)
        if not success:
            logger.error(f"发送任务到Kafka失败: {task.id}")
            # 如果发送失败，更新任务状态
            task.status = "FAILED"
            task.error_message = "发送任务到队列失败"
            await self.db.commit()
        
        # 确保在返回之前刷新对象状态
        await self.db.refresh(task)
        
        return task

    async def get_tasks(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Task]:
        """获取任务列表"""
        query = select(Task).order_by(desc(Task.created_at))
        
        if status:
            query = query.filter(Task.status == status)
        if task_type:
            query = query.filter(Task.task_type == task_type)
        if user_id:
            query = query.filter(Task.user_id == user_id)
            
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_tasks_paginated(
        self,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        task_name: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> TaskListResponse:
        """获取分页任务列表"""
        # 构建查询条件
        query = select(Task).order_by(desc(Task.created_at))
        count_query = select(func.count(Task.id))
        
        if status:
            query = query.filter(Task.status == status)
            count_query = count_query.filter(Task.status == status)
        if task_type:
            query = query.filter(Task.task_type == task_type)
            count_query = count_query.filter(Task.task_type == task_type)
        if task_name:
            query = query.filter(Task.task_name.like(f"%{task_name}%"))
            count_query = count_query.filter(Task.task_name.like(f"%{task_name}%"))
        if user_id:
            query = query.filter(Task.user_id == user_id)
            count_query = count_query.filter(Task.user_id == user_id)
        
        # 获取总数
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 获取分页数据
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)
        result = await self.db.execute(query)
        tasks = result.scalars().all()
        
        # 构建响应
        response = TaskListResponse.create(tasks, total, page, size)
        
        return response

    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务详情"""
        result = await self.db.execute(select(Task).filter(Task.id == task_id))
        task = result.scalars().first()

        return task

    async def get_task_by_name(self, task_name: str, user_id: str) -> Optional[Task]:
        """根据任务名称和用户ID获取任务"""
        result = await self.db.execute(
            select(Task).filter(Task.task_name == task_name, Task.user_id == user_id)
        )
        return result.scalars().first()

    async def update_task(self, task_id: str, task_data: TaskUpdate) -> Optional[Task]:
        """更新任务信息"""
        update_data = task_data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.now()
            
        await self.db.execute(
            update(Task)
            .where(Task.id == task_id)
            .values(**update_data)
        )
        await self.db.commit()
        
        return await self.get_task(task_id)

    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        result = await self.db.execute(
            delete(Task).where(Task.id == task_id)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def start_task(self, task_id: str) -> Optional[Task]:
        """启动任务"""
        task = await self.get_task(task_id)
        if not task:
            return None
            
        if task.status != "PENDING":
            return task
            
        # 更新任务状态
        updated_task = await self.update_task(
            task_id, 
            TaskUpdate(status="RUNNING")
        )
        
        # 将任务发送到Kafka队列
        task_message = {
            "task_id": task.id,
            "task_name": task.task_name,
            "task_type": task.task_type,
            "parameters": task.parameters,
            "account_id": task.account_id,
            "proxy_id": task.proxy_id,
            "user_id": task.user_id,
            "created_at": datetime.now().isoformat()
        }
        
        success = await kafka_client.send_task(task_message)
        if success:
            logger.info(f"任务 {task_id} 已发送到Kafka队列")
        else:
            logger.error(f"发送任务到Kafka失败: {task_id}")
            # 如果发送失败，更新任务状态
            await self.update_task(
                task_id,
                TaskUpdate(status="FAILED", error_message="发送任务到队列失败")
            )
            
        return updated_task

    async def stop_task(self, task_id: str) -> Optional[Task]:
        """停止任务"""
        task = await self.get_task(task_id)
        if not task:
            return None
            
        if task.status not in ["PENDING", "RUNNING"]:
            return task
            
        # 更新任务状态
        updated_task = await self.update_task(
            task_id, 
            TaskUpdate(status="STOPPING")
        )
        
        # 发送停止任务的控制消息到Kafka
        control_message = {
            "action": "STOP_TASK",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        }
        
        success = await kafka_client.send_control(control_message)
        if success:
            logger.info(f"停止任务 {task_id} 的控制消息已发送到Kafka队列")
        else:
            logger.error(f"发送停止任务控制消息失败: {task_id}")
            
        # 无论消息是否发送成功，都将状态更新为已停止
        # 因为worker可能已经完成或者失败，或者根本没有收到任务
        return await self.update_task(
            task_id, 
            TaskUpdate(status="STOPPED")
        )