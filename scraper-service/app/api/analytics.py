from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.database import get_db
from app.services.task_analytics import TaskAnalyticsService
from app.schemas.analytics import AnalyticsResponse, TimeGranularity

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analytics"])


@router.get("/realtime", response_model=AnalyticsResponse)
async def get_realtime_task_analytics(
    db: AsyncSession = Depends(get_db)
):
    """获取实时任务分析数据"""
    try:
        analytics_service = TaskAnalyticsService(db)
        result = await analytics_service.get_realtime_analytics()
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.message)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实时任务分析数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取实时任务分析数据失败: {str(e)}")


@router.get("/history", response_model=AnalyticsResponse)
async def get_history_task_analytics(
    time_range: str = Query("24h", description="时间范围 (1h, 24h, 7d, 30d)"),
    task_type: Optional[str] = Query(None, description="任务类型筛选"),
    status: Optional[str] = Query(None, description="执行状态筛选"),
    db: AsyncSession = Depends(get_db)
):
    """获取历史任务分析数据"""
    try:
        analytics_service = TaskAnalyticsService(db)
        result = await analytics_service.get_history_analytics(time_range, task_type, status)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.message)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取历史任务分析数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史任务分析数据失败: {str(e)}")


@router.get("/efficiency", response_model=AnalyticsResponse)
async def get_task_efficiency_stats(
    task_id: Optional[str] = Query(None, description="任务ID，不提供则返回汇总统计"),
    db: AsyncSession = Depends(get_db)
):
    """获取任务效率统计"""
    try:
        analytics_service = TaskAnalyticsService(db)
        result = await analytics_service.get_task_efficiency_stats(task_id)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.message)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务效率统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务效率统计失败: {str(e)}")


@router.get("/trends", response_model=AnalyticsResponse)
async def get_task_trends(
    time_range: str = Query("24h", description="时间范围 (1h, 24h, 7d, 30d)"),
    task_type: Optional[str] = Query(None, description="任务类型筛选"),
    status: Optional[str] = Query(None, description="执行状态筛选"),
    db: AsyncSession = Depends(get_db)
):
    """获取任务趋势数据"""
    try:
        analytics_service = TaskAnalyticsService(db)
        result = await analytics_service.get_task_trends(time_range, task_type, status)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.message)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务趋势数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务趋势数据失败: {str(e)}")


@router.post("/cache/invalidate")
async def invalidate_task_analytics_cache(
    db: AsyncSession = Depends(get_db)
):
    """清除任务分析缓存"""
    try:
        analytics_service = TaskAnalyticsService(db)
        await analytics_service.invalidate_task_analytics_cache()
        
        return AnalyticsResponse(
            success=True,
            message="任务分析缓存清除成功"
        )
        
    except Exception as e:
        logger.error(f"清除任务分析缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"清除任务分析缓存失败: {str(e)}")


# 任务相关活动端点
@router.get("/activities/recent", response_model=AnalyticsResponse)
async def get_recent_task_activities(
    limit: int = Query(10, ge=1, le=100, description="返回活动数量限制"),
    db: AsyncSession = Depends(get_db)
):
    """获取最近的任务相关活动"""
    try:
        analytics_service = TaskAnalyticsService(db)
        
        # 获取最近任务活动
        recent_activities = await analytics_service.get_recent_task_activities(limit)
        
        return AnalyticsResponse(
            success=True,
            message="最近任务活动获取成功",
            data=recent_activities
        )
        
    except Exception as e:
        logger.error(f"获取最近任务活动失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取最近任务活动失败: {str(e)}")