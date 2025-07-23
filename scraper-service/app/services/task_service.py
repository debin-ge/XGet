from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, desc
from ..models.task import Task
from ..schemas.task import TaskCreate, TaskUpdate
import uuid
from datetime import datetime
import httpx
import json
import asyncio
from ..core.config import settings


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, task_data: TaskCreate) -> Task:
        """创建采集任务"""
        task = Task(
            id=str(uuid.uuid4()),
            task_type=task_data.task_type,
            parameters=task_data.parameters,
            account_id=task_data.account_id,
            proxy_id=task_data.proxy_id,
            status="PENDING",
            progress=0.0,
            result_count=0
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        
        # 发送任务到Kafka
        try:
            from aiokafka import AIOKafkaProducer
            producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await producer.start()
            try:
                await producer.send_and_wait(
                    settings.KAFKA_TOPIC_TASKS,
                    {
                        "task_id": task.id,
                        "task_type": task.task_type,
                        "parameters": task.parameters,
                        "account_id": task.account_id,
                        "proxy_id": task.proxy_id
                    }
                )
            finally:
                await producer.stop()
        except Exception as e:
            print(f"发送任务到Kafka失败: {e}")
            # 如果发送失败，更新任务状态
            task.status = "FAILED"
            task.error_message = f"发送任务到队列失败: {str(e)}"
            await self.db.commit()
            
        return task

    async def get_tasks(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        status: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> List[Task]:
        """获取任务列表"""
        query = select(Task).order_by(desc(Task.created_at))
        
        if status:
            query = query.filter(Task.status == status)
        if task_type:
            query = query.filter(Task.task_type == task_type)
            
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务详情"""
        result = await self.db.execute(select(Task).filter(Task.id == task_id))
        return result.scalars().first()

    async def update_task(self, task_id: str, task_data: TaskUpdate) -> Optional[Task]:
        """更新任务信息"""
        update_data = task_data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.now()
        
        # 如果状态变为RUNNING，设置started_at
        if task_data.status == "RUNNING":
            update_data["started_at"] = datetime.now()
            
        # 如果状态变为COMPLETED或FAILED，设置completed_at
        if task_data.status in ["COMPLETED", "FAILED"]:
            update_data["completed_at"] = datetime.now()
            
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
        return await self.update_task(
            task_id, 
            TaskUpdate(status="RUNNING", progress=0.0)
        )

    async def stop_task(self, task_id: str) -> Optional[Task]:
        """停止任务"""
        task = await self.get_task(task_id)
        if not task:
            return None
            
        if task.status not in ["PENDING", "RUNNING"]:
            return task
            
        # 更新任务状态
        return await self.update_task(
            task_id, 
            TaskUpdate(status="STOPPED")
        )

    async def get_account_info(self, account_id: str) -> Optional[Dict]:
        """获取账号信息"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{settings.ACCOUNT_SERVICE_URL}/accounts/{account_id}"
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                print(f"获取账号信息失败: {e}")
        return None

    async def get_proxy_info(self, proxy_id: str) -> Optional[Dict]:
        """获取代理信息"""
        if not proxy_id:
            return None
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{settings.PROXY_SERVICE_URL}/proxies/{proxy_id}"
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                print(f"获取代理信息失败: {e}")
        return None