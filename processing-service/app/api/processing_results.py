from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.database import get_db
from ..models.processing_result import ProcessingResult
from ..schemas.processing_result import (
    ProcessingResultCreate,
    ProcessingResultUpdate,
    ProcessingResultResponse,
    ProcessingResultList,
)
from ..services.result_service import ResultService

router = APIRouter()

@router.post("", response_model=ProcessingResultResponse, status_code=status.HTTP_201_CREATED)
async def create_processing_result(
    result_data: ProcessingResultCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    创建新的数据处理结果
    """
    service = ResultService()
    result = await service.create_result(db, result_data)
    return result

@router.get("", response_model=ProcessingResultList)
async def get_processing_results(
    skip: int = 0,
    limit: int = 100,
    task_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    获取处理结果列表，支持分页和过滤
    """
    service = ResultService()
    results, total = await service.get_results(db, skip, limit, task_id)
    return {
        "results": results,
        "total": total,
    }

@router.get("/{result_id}", response_model=ProcessingResultResponse)
async def get_processing_result(result_id: str, db: AsyncSession = Depends(get_db)):
    """
    获取指定ID的处理结果
    """
    service = ResultService()
    result = await service.get_result(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="处理结果未找到")
    return result

@router.get("/task/{task_id}", response_model=ProcessingResultResponse)
async def get_result_by_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    获取指定任务的处理结果
    """
    service = ResultService()
    result = await service.get_result_by_task(db, task_id)
    if not result:
        raise HTTPException(status_code=404, detail="处理结果未找到")
    return result

@router.put("/{result_id}", response_model=ProcessingResultResponse)
async def update_processing_result(
    result_id: str, result_data: ProcessingResultUpdate, db: AsyncSession = Depends(get_db)
):
    """
    更新处理结果信息（仅限元数据和存储位置）
    """
    service = ResultService()
    result = await service.update_result(db, result_id, result_data)
    if not result:
        raise HTTPException(status_code=404, detail="处理结果未找到")
    return result

@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_processing_result(result_id: str, db: AsyncSession = Depends(get_db)):
    """
    删除处理结果（仅限管理操作）
    """
    service = ResultService()
    success = await service.delete_result(db, result_id)
    if not success:
        raise HTTPException(status_code=404, detail="处理结果未找到")

@router.get("/stats", response_model=Dict[str, Any])
async def get_processing_stats(
    period: str = "daily",
    date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    获取处理统计信息
    """
    service = ResultService()
    stats = await service.get_stats(db, period, date)
    return stats 