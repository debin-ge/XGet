from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional

from app.db.session import get_db
from app.schemas.analytics import AnalyticsResponse
from app.services.task_analysis import task_analysis_service

router = APIRouter()


@router.get("/realtime", response_model=AnalyticsResponse)
async def get_tasks_realtime_analytics(
    db: AsyncSession = Depends(get_db)
):
    """获取任务实时统计数据"""
    try:
        data = await task_analysis_service.get_realtime_analytics()
        return AnalyticsResponse(
            success=True,
            message="Task real-time analytics retrieved successfully",
            data=data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=AnalyticsResponse)
async def get_tasks_history_analytics(
    time_range: str = "24h",
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取任务历史统计数据"""
    try:
        data = await task_analysis_service.get_history_analytics(
            time_range=time_range,
            task_type=task_type,
            status=status
        )
        return AnalyticsResponse(
            success=True,
            message="Task history analytics retrieved successfully",
            data=data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/efficiency", response_model=AnalyticsResponse)
async def get_task_efficiency_stats(
    task_id: str = None
):
    """获取任务效率统计"""
    try:
        data = await task_analysis_service.get_task_efficiency_stats(task_id)
        return AnalyticsResponse(
            success=True,
            message="Task efficiency stats retrieved successfully",
            data=data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends", response_model=AnalyticsResponse)
async def get_task_trends(
    time_range: str = "7d",
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取任务趋势统计数据"""
    try:
        data = await task_analysis_service.get_task_trends(
            time_range=time_range,
            task_type=task_type,
            status=status
        )
        return AnalyticsResponse(
            success=True,
            message="Task trends retrieved successfully",
            data=data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))