from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.database import get_db
from ..models.processing_task import ProcessingTask
from ..schemas.processing_task import (
    ProcessingTaskCreate,
    ProcessingTaskUpdate,
    ProcessingTaskResponse,
    ProcessingTaskList,
)
from ..services.processing_service import ProcessingService

router = APIRouter()

@router.post("", response_model=ProcessingTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_processing_task(
    task_data: ProcessingTaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    创建新的数据处理任务
    """
    service = ProcessingService()
    task = await service.create_task(db, task_data)
    
    # 如果优先级为高，立即在后台开始处理
    if task_data.priority == "high":
        background_tasks.add_task(
            service.process_request,
            {
                "id": task.id,
                "task_type": task.task_type,
                "source_data_id": task.source_data_id,
                "callback_url": task.callback_url,
            }
        )
    
    return task

@router.get("", response_model=ProcessingTaskList)
async def get_processing_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    获取处理任务列表，支持分页和过滤
    """
    service = ProcessingService()
    tasks, total = await service.get_tasks(db, skip, limit, status, task_type)
    return {
        "tasks": tasks,
        "total": total,
        "page": skip // limit + 1,
        "page_size": limit,
    }

@router.get("/{task_id}", response_model=ProcessingTaskResponse)
async def get_processing_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    获取指定ID的处理任务
    """
    service = ProcessingService()
    task = await service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="处理任务未找到")
    return task

@router.put("/{task_id}", response_model=ProcessingTaskResponse)
async def update_processing_task(
    task_id: str, task_data: ProcessingTaskUpdate, db: AsyncSession = Depends(get_db)
):
    """
    更新处理任务信息
    """
    service = ProcessingService()
    task = await service.update_task(db, task_id, task_data)
    if not task:
        raise HTTPException(status_code=404, detail="处理任务未找到")
    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_processing_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    删除处理任务（仅限未开始的任务）
    """
    service = ProcessingService()
    success = await service.delete_task(db, task_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="无法删除任务，任务可能不存在或已经开始处理"
        ) 