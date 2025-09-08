from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List

from app.db.session import get_db
from app.schemas.analytics import AnalyticsResponse
from app.services.account_analysis import account_analysis_service

router = APIRouter()


@router.get("/realtime", response_model=AnalyticsResponse)
async def get_accounts_realtime_analytics():
    """获取账户实时统计数据"""
    try:
        data = await account_analysis_service.get_realtime_analytics()
        return AnalyticsResponse(
            success=True,
            message="Account real-time analytics retrieved successfully",
            data=data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=AnalyticsResponse)
async def get_accounts_history_analytics(
    time_range: str = "24h"
):
    """获取账户历史统计数据"""
    try:
        data = await account_analysis_service.get_history_analytics(
            time_range=time_range,
        )
        return AnalyticsResponse(
            success=True,
            message="Account history analytics retrieved successfully",
            data=data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage", response_model=AnalyticsResponse)
async def get_account_usage_stats(
    account_id: Optional[str] = None
):
    """获取账户使用统计"""
    try:
        data = await account_analysis_service.get_account_usage_stats(account_id)
        return AnalyticsResponse(
            success=True,
            message="Account usage stats retrieved successfully",
            data=data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))