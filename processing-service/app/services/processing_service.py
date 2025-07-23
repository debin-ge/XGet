import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import httpx
from sqlalchemy import select, update, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..models.processing_task import ProcessingTask
from ..models.processing_result import ProcessingResult
from ..models.processing_rule import ProcessingRule
from ..schemas.processing_task import ProcessingTaskCreate, ProcessingTaskUpdate
from ..schemas.processing_result import ProcessingResultCreate
from ..core.config import settings
from ..db.database import mongo_db

logger = logging.getLogger(__name__)

class ProcessingService:
    """数据处理服务"""
    
    async def create_task(self, db: AsyncSession, task_data: ProcessingTaskCreate) -> ProcessingTask:
        """创建新的处理任务"""
        task_id = str(uuid.uuid4())
        task = ProcessingTask(
            id=task_id,
            task_type=task_data.task_type,
            source_data_id=task_data.source_data_id,
            parameters=task_data.parameters,
            priority=task_data.priority,
            callback_url=task_data.callback_url,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        logger.info(f"创建处理任务: {task_id}")
        return task
    
    async def get_task(self, db: AsyncSession, task_id: str) -> Optional[ProcessingTask]:
        """获取指定ID的处理任务"""
        query = select(ProcessingTask).where(ProcessingTask.id == task_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_tasks(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> Tuple[List[ProcessingTask], int]:
        """获取处理任务列表"""
        # 构建查询
        query = select(ProcessingTask)
        count_query = select(func.count()).select_from(ProcessingTask)
        
        # 应用过滤条件
        if status:
            query = query.where(ProcessingTask.status == status)
            count_query = count_query.where(ProcessingTask.status == status)
        if task_type:
            query = query.where(ProcessingTask.task_type == task_type)
            count_query = count_query.where(ProcessingTask.task_type == task_type)
        
        # 应用排序和分页
        query = query.order_by(desc(ProcessingTask.created_at)).offset(skip).limit(limit)
        
        # 执行查询
        result = await db.execute(query)
        count_result = await db.execute(count_query)
        
        return result.scalars().all(), count_result.scalar_one()
    
    async def update_task(
        self, db: AsyncSession, task_id: str, task_data: ProcessingTaskUpdate
    ) -> Optional[ProcessingTask]:
        """更新处理任务信息"""
        # 获取现有任务
        task = await self.get_task(db, task_id)
        if not task:
            return None
        
        # 更新任务数据
        update_data = task_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)
        
        # 如果状态变更为进行中，设置开始时间
        if task_data.status == "processing" and not task.started_at:
            task.started_at = datetime.utcnow()
        
        # 如果状态变更为已完成或失败，设置完成时间
        if task_data.status in ["completed", "failed"] and not task.completed_at:
            task.completed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(task)
        logger.info(f"更新处理任务: {task_id}, 状态: {task.status}")
        return task
    
    async def delete_task(self, db: AsyncSession, task_id: str) -> bool:
        """删除处理任务（仅限未开始的任务）"""
        task = await self.get_task(db, task_id)
        if not task or task.status not in ["pending", "failed"]:
            return False
        
        await db.delete(task)
        await db.commit()
        logger.info(f"删除处理任务: {task_id}")
        return True
    
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
        
        # 更新任务的结果ID
        task_query = select(ProcessingTask).where(ProcessingTask.id == result_data.task_id)
        task_result = await db.execute(task_query)
        task = task_result.scalar_one_or_none()
        if task:
            task.result_id = result_id
        
        await db.commit()
        await db.refresh(result)
        logger.info(f"创建处理结果: {result_id} 对应任务: {result_data.task_id}")
        return result
    
    async def get_result(self, db: AsyncSession, result_id: str) -> Optional[ProcessingResult]:
        """获取指定ID的处理结果"""
        query = select(ProcessingResult).where(ProcessingResult.id == result_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_result_by_task(self, db: AsyncSession, task_id: str) -> Optional[ProcessingResult]:
        """获取指定任务的处理结果"""
        query = select(ProcessingResult).where(ProcessingResult.task_id == task_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def process_raw_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理原始数据"""
        try:
            # 获取数据ID和类型
            data_id = data.get("id")
            data_type = data.get("type")
            
            logger.info(f"处理原始数据: {data_id}, 类型: {data_type}")
            
            # 根据数据类型应用不同的处理逻辑
            processed_data = await self._apply_processing_rules(data)
            
            # 将处理后的数据发送到存储服务
            result = await self._send_to_storage_service(processed_data)
            
            return result
        except Exception as e:
            logger.error(f"处理数据时出错: {str(e)}", exc_info=True)
            return {"error": str(e), "status": "failed"}
    
    async def process_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理特定处理请求"""
        try:
            # 获取请求ID和类型
            request_id = data.get("id")
            task_type = data.get("task_type")
            
            logger.info(f"处理请求: {request_id}, 类型: {task_type}")
            
            # 获取源数据
            source_data = await self._get_source_data(data.get("source_data_id"))
            if not source_data:
                return {"error": "无法获取源数据", "status": "failed"}
            
            # 应用处理规则
            processed_data = await self._apply_processing_rules(source_data, task_type=task_type)
            
            # 将处理后的数据发送到存储服务
            result = await self._send_to_storage_service(processed_data)
            
            # 如果有回调URL，发送处理结果
            callback_url = data.get("callback_url")
            if callback_url:
                await self._send_callback(callback_url, result)
            
            return result
        except Exception as e:
            logger.error(f"处理请求时出错: {str(e)}", exc_info=True)
            return {"error": str(e), "status": "failed"}
    
    async def _apply_processing_rules(
        self, data: Dict[str, Any], task_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """应用处理规则到数据"""
        # 这里实现具体的数据处理逻辑
        # 根据数据类型和任务类型应用不同的处理规则
        
        # 示例：简单的文本处理
        if "text" in data:
            # 文本清洗
            text = data["text"]
            # 移除多余空格
            text = " ".join(text.split())
            # 更新数据
            data["text"] = text
            
            # 如果是文本分析任务，添加额外的分析数据
            if task_type == "TEXT_ANALYSIS":
                # 计算基本统计信息
                word_count = len(text.split())
                char_count = len(text)
                data["analysis"] = {
                    "word_count": word_count,
                    "char_count": char_count,
                    "processed": True,
                    "processing_timestamp": datetime.utcnow().isoformat()
                }
        
        # 添加处理元数据
        if "metadata" not in data:
            data["metadata"] = {}
        
        data["metadata"]["processed"] = True
        data["metadata"]["processing_timestamp"] = datetime.utcnow().isoformat()
        data["metadata"]["processor_version"] = "1.0.0"
        
        return data
    
    async def _get_source_data(self, source_id: str) -> Optional[Dict[str, Any]]:
        """从数据采集服务获取源数据"""
        try:
            # 构建API请求
            url = f"{settings.SCRAPER_SERVICE_URL}/results/{source_id}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"获取源数据时出错: {str(e)}", exc_info=True)
            return None
    
    async def _send_to_storage_service(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """将处理后的数据发送到存储服务"""
        try:
            # 构建存储请求
            storage_request = {
                "data_type": data.get("type", "PROCESSED_DATA"),
                "content": data,
                "metadata": data.get("metadata", {}),
                "storage_options": {
                    "compression": True,
                    "encryption": False,
                    "replication": 1
                }
            }
            
            # 发送到存储服务
            url = f"{settings.STORAGE_SERVICE_URL}/storage"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=storage_request)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"发送数据到存储服务时出错: {str(e)}", exc_info=True)
            # 如果存储服务不可用，将数据保存到MongoDB作为备份
            if mongo_db:
                try:
                    collection = mongo_db.processed_data
                    data["_backup_timestamp"] = datetime.utcnow().isoformat()
                    result = await collection.insert_one(data)
                    return {"id": str(result.inserted_id), "status": "backup_stored"}
                except Exception as mongo_err:
                    logger.error(f"备份到MongoDB时出错: {str(mongo_err)}", exc_info=True)
            
            return {"error": str(e), "status": "storage_failed"}
    
    async def _send_callback(self, callback_url: str, result: Dict[str, Any]) -> None:
        """发送处理结果到回调URL"""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(callback_url, json=result)
                logger.info(f"已发送回调到: {callback_url}")
        except Exception as e:
            logger.error(f"发送回调时出错: {str(e)}", exc_info=True) 