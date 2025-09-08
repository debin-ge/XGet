from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.database import get_db
from app.services.proxy_analytics import ProxyAnalyticsService
from app.schemas.analytics import AnalyticsResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analytics"])


@router.get("/realtime", response_model=AnalyticsResponse)
async def get_realtime_proxy_analytics(
    db: AsyncSession = Depends(get_db)
):
    """获取实时代理分析数据"""
    try:
        analytics_service = ProxyAnalyticsService(db)
        result = await analytics_service.get_realtime_analytics()
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.message)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实时代理分析数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取实时代理分析数据失败: {str(e)}")


@router.get("/history", response_model=AnalyticsResponse)
async def get_history_proxy_analytics(
    time_range: str = Query("24h", description="时间范围 (1h, 24h, 7d, 30d)"),
    country: Optional[str] = Query(None, description="国家代码筛选"),
    isp: Optional[str] = Query(None, description="ISP名称筛选"),
    db: AsyncSession = Depends(get_db)
):
    """获取历史代理分析数据"""
    try:
        analytics_service = ProxyAnalyticsService(db)
        result = await analytics_service.get_history_analytics(time_range, country, isp)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.message)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取历史代理分析数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史代理分析数据失败: {str(e)}")


@router.get("/quality", response_model=AnalyticsResponse)
async def get_proxy_quality_stats(
    proxy_id: Optional[str] = Query(None, description="代理ID，不提供则返回汇总统计"),
    db: AsyncSession = Depends(get_db)
):
    """获取代理质量统计"""
    try:
        analytics_service = ProxyAnalyticsService(db)
        result = await analytics_service.get_proxy_quality_stats(proxy_id)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.message)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取代理质量统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取代理质量统计失败: {str(e)}")


@router.post("/cache/invalidate")
async def invalidate_proxy_analytics_cache(
    db: AsyncSession = Depends(get_db)
):
    """清除代理分析缓存"""
    try:
        analytics_service = ProxyAnalyticsService(db)
        await analytics_service.invalidate_proxy_analytics_cache()
        
        return AnalyticsResponse(
            success=True,
            message="代理分析缓存清除成功"
        )
        
    except Exception as e:
        logger.error(f"清除代理分析缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"清除代理分析缓存失败: {str(e)}")


# 代理相关活动端点
@router.get("/activities/recent", response_model=AnalyticsResponse)
async def get_recent_proxy_activities(
    limit: int = Query(10, ge=1, le=100, description="返回活动数量限制"),
    db: AsyncSession = Depends(get_db)
):
    """获取最近的代理相关活动"""
    try:
        analytics_service = ProxyAnalyticsService(db)
        
        # 获取最近代理活动
        recent_activities = await analytics_service.get_recent_proxy_activities(limit)
        
        return AnalyticsResponse(
            success=True,
            message="最近代理活动获取成功",
            data=recent_activities
        )
        
    except Exception as e:
        logger.error(f"获取最近代理活动失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取最近代理活动失败: {str(e)}")