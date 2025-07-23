from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from ..db.database import get_db
from ..services.task_execution_service import TaskExecutionService
from ..schemas.task_execution import TaskExecutionCreate, TaskExecutionUpdate, TaskExecutionResponse

router = APIRouter()


@router.post("/", response_model=TaskExecutionResponse)
async def create_task_execution(
    execution_data: TaskExecutionCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建任务执行记录"""
    service = TaskExecutionService(db)
    execution = await service.create_execution(execution_data)
    return execution


@router.get("/{execution_id}", response_model=TaskExecutionResponse)
async def get_task_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取任务执行记录"""
    service = TaskExecutionService(db)
    execution = await service.get_execution(execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task execution with ID {execution_id} not found"
        )
    return execution


@router.get("/task/{task_id}", response_model=List[TaskExecutionResponse])
async def get_task_executions(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取任务的所有执行记录"""
    service = TaskExecutionService(db)
    executions = await service.get_executions_by_task(task_id)
    return executions


@router.put("/{execution_id}", response_model=TaskExecutionResponse)
async def update_task_execution(
    execution_id: str,
    execution_data: TaskExecutionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新任务执行记录"""
    service = TaskExecutionService(db)
    execution = await service.update_execution(execution_id, execution_data)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task execution with ID {execution_id} not found"
        )
    return execution


@router.post("/{execution_id}/complete", response_model=TaskExecutionResponse)
async def complete_task_execution(
    execution_id: str,
    status: str,
    error_message: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """完成任务执行记录"""
    service = TaskExecutionService(db)
    execution = await service.complete_execution(execution_id, status, error_message)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task execution with ID {execution_id} not found"
        )
    return execution 