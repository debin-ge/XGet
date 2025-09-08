from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional

from app.db.session import get_db
from app.schemas.analytics import AnalyticsResponse
from app.services.proxy_analysis import proxy_analysis_service

router = APIRouter()


@router.get("/realtime", response_model=AnalyticsResponse)
async def get_proxies_realtime_analytics():
    """获取代理实时统计数据"""
    try:
        data = await proxy_analysis_service.get_realtime_analytics()
        return AnalyticsResponse(
            success=True,
            message="Proxy real-time analytics retrieved successfully",
            data=data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=AnalyticsResponse)
async def get_proxies_history_analytics(
    time_range: str = "24h",
    country: Optional[str] = None,
    isp: Optional[str] = None
):
    """获取代理历史统计数据"""
    try:
        data = await proxy_analysis_service.get_history_analytics(
            time_range=time_range,
            country=country,
            isp=isp
        )
        return AnalyticsResponse(
            success=True,
            message="Proxy history analytics retrieved successfully",
            data=data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality", response_model=AnalyticsResponse)
async def get_proxy_quality_stats(
    proxy_id: Optional[str] = None
):
    """获取代理质量统计"""
    try:
        data = await proxy_analysis_service.get_proxy_quality_stats(proxy_id)
        return AnalyticsResponse(
            success=True,
            message="Proxy quality stats retrieved successfully",
            data=data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))