from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from datetime import datetime

from ..db.database import get_db
from ..schemas.proxy import (
    ProxyCreate, ProxyUpdate, ProxyResponse, 
    ProxyCheck, ProxyCheckResponse, ProxyCheckResult,
    ProxyImport, ProxyImportResponse, ProxyImportResult,
    ProxyQualityResponse, ProxyQualityUpdate, ProxyUsageResult,
    ProxyUsageHistoryCreate, ProxyUsageHistoryResponse,
    ProxyUsageHistoryListResponse, ProxyUsageHistoryFilter,
    ProxyListResponse, ProxyQualityListResponse,
    ProxyQualityInfoResponse, ProxyQualityInfoListResponse
)
from ..services.proxy_service import ProxyService
import csv
import io

router = APIRouter()

@router.post("/", response_model=ProxyResponse, status_code=status.HTTP_201_CREATED)
async def create_proxy(
    proxy: ProxyCreate, 
    db: AsyncSession = Depends(get_db)
):
    """创建新代理"""
    service = ProxyService(db)
    return await service.create_proxy(proxy)

@router.get("/", response_model=ProxyListResponse)
async def get_proxies(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="代理状态筛选"),
    country: Optional[str] = Query(None, description="国家筛选"),
    ip: Optional[str] = Query(None, description="IP筛选"),
    db: AsyncSession = Depends(get_db)
):
    """获取代理列表"""
    service = ProxyService(db)
    return await service.get_proxies_paginated(page, size, status, country, ip)

@router.get("/quality-info", response_model=ProxyQualityInfoListResponse)
async def get_proxies_quality_info(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="代理状态筛选"),
    country: Optional[str] = Query(None, description="国家筛选"),
    min_quality_score: Optional[float] = Query(None, ge=0, le=1, description="最小质量分数筛选"),
    ip: Optional[str] = Query(None, description="IP筛选"),
    db: AsyncSession = Depends(get_db)
):
    """获取代理质量信息列表（包含IP+port、检测成功率、使用次数、成功次数、质量分数、最近使用时间等）"""
    service = ProxyService(db)
    
    quality_info_list, total = await service.get_proxies_quality_info(
        page=page,
        size=size,
        status=status,
        country=country,
        min_quality_score=min_quality_score,
        ip=ip
    )
    
    # 计算总页数
    pages = (total + size - 1) // size if total > 0 else 0
    
    return ProxyQualityInfoListResponse(
        total=total,
        items=quality_info_list,
        page=page,
        size=size,
        pages=pages
    )

@router.get("/{proxy_id}", response_model=ProxyResponse)
async def get_proxy(
    proxy_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """获取代理详情"""
    service = ProxyService(db)
    proxy = await service.get_proxy(proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    return proxy

@router.put("/{proxy_id}", response_model=ProxyResponse)
async def update_proxy(
    proxy_id: str, 
    proxy_data: ProxyUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """更新代理信息"""
    service = ProxyService(db)
    proxy = await service.update_proxy(proxy_id, proxy_data)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    return proxy

@router.delete("/{proxy_id}", response_model=Dict)
async def delete_proxy(
    proxy_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """删除代理"""
    service = ProxyService(db)
    success = await service.delete_proxy(proxy_id)
    if not success:
        raise HTTPException(status_code=404, detail="Proxy not found")
    return {"message": "Proxy deleted successfully"}

@router.post("/check", response_model=ProxyCheckResponse)
async def check_proxies(
    check_data: ProxyCheck,
    db: AsyncSession = Depends(get_db)
):
    """检查代理可用性"""
    service = ProxyService(db)
    results = await service.check_proxies(check_data.proxy_ids)
    
    active_count = sum(1 for r in results if r.status == "ACTIVE")
    inactive_count = len(results) - active_count
    
    return ProxyCheckResponse(
        total=len(check_data.proxy_ids),
        checked=len(results),
        active=active_count,
        inactive=inactive_count,
        results=results
    )

@router.post("/{proxy_id}/check", response_model=ProxyCheckResult)
async def check_single_proxy(
    proxy_id: str,
    db: AsyncSession = Depends(get_db)
):
    """检查单个代理可用性"""
    service = ProxyService(db)
    proxy = await service.get_proxy(proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    
    result = await service.check_proxy(proxy)
    return result

@router.get("/stats/summary", response_model=Dict)
async def get_proxy_stats(
    db: AsyncSession = Depends(get_db)
):
    """获取代理统计信息"""
    service = ProxyService(db)
    
    # 获取所有代理
    all_proxies = await service.get_proxies(limit=10000)
    
    # 统计信息
    total = len(all_proxies)
    active = sum(1 for p in all_proxies if p.status == "ACTIVE")
    inactive = sum(1 for p in all_proxies if p.status == "INACTIVE")
    checking = sum(1 for p in all_proxies if p.status == "CHECKING")
    
    # 按国家分组
    countries = {}
    for proxy in all_proxies:
        if proxy.country:
            if proxy.country not in countries:
                countries[proxy.country] = 0
            countries[proxy.country] += 1
    
    # 按类型分组
    types = {}
    for proxy in all_proxies:
        if proxy.type not in types:
            types[proxy.type] = 0
        types[proxy.type] += 1
    
    # 性能统计
    latency_avg = 0
    latency_count = 0
    success_rate_avg = 0
    success_rate_count = 0
    
    for proxy in all_proxies:
        if proxy.latency is not None:
            latency_avg += proxy.latency
            latency_count += 1
        if proxy.success_rate is not None:
            success_rate_avg += proxy.success_rate
            success_rate_count += 1
    
    if latency_count > 0:
        latency_avg /= latency_count
    if success_rate_count > 0:
        success_rate_avg /= success_rate_count
    
    return {
        "total": total,
        "status": {
            "active": active,
            "inactive": inactive,
            "checking": checking
        },
        "countries": countries,
        "types": types,
        "performance": {
            "avg_latency": round(latency_avg, 2),
            "avg_success_rate": round(success_rate_avg, 2)
        }
    }

@router.post("/rotate", response_model=ProxyResponse)
async def rotate_proxy(
    country: Optional[str] = None,
    max_latency: Optional[int] = None,
    min_success_rate: Optional[float] = 0.5,
    min_quality_score: Optional[float] = 0.6,
    db: AsyncSession = Depends(get_db)
):
    """轮换代理（获取一个高质量可用代理）"""
    service = ProxyService(db)
    
    # 获取轮换代理
    proxy = await service.get_rotating_proxy(
        country=country,
        max_latency=max_latency,
        min_success_rate=min_success_rate,
        min_quality_score=min_quality_score
    )
    
    if not proxy:
        raise HTTPException(status_code=404, detail="No available proxy found")
    
    return proxy

@router.get("/{proxy_id}/quality", response_model=ProxyQualityResponse)
async def get_proxy_quality(
    proxy_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取代理质量详情"""
    service = ProxyService(db)
    
    quality = await service.get_proxy_quality(proxy_id)
    if not quality:
        raise HTTPException(status_code=404, detail="Proxy quality not found")
    
    return quality

@router.put("/{proxy_id}/quality", response_model=ProxyQualityResponse)
async def update_proxy_quality(
    proxy_id: str,
    quality_data: ProxyQualityUpdate,
    db: AsyncSession = Depends(get_db)
):
    """手动更新代理质量信息"""
    service = ProxyService(db)
    
    # 检查代理是否存在
    proxy = await service.get_proxy(proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
        
    quality = await service.update_proxy_quality(proxy_id, quality_data)
    if not quality:
        raise HTTPException(status_code=404, detail="Proxy quality not found")
    
    return quality

@router.post("/batch-check", response_model=Dict)
async def batch_check_proxies(
    limit: int = Query(100, description="检查代理数量"),
    db: AsyncSession = Depends(get_db)
):
    """批量检查代理可用性（按最后检查时间排序）"""
    service = ProxyService(db)
    
    # 获取需要检查的代理
    proxies = await service.get_proxies_for_check(limit)
    
    if not proxies:
        return {"message": "No proxies to check", "checked": 0}
    
    # 检查代理
    proxy_ids = [p.id for p in proxies]
    results = await service.check_proxies(proxy_ids)
    
    active_count = sum(1 for r in results if r.status == "ACTIVE")
    inactive_count = len(results) - active_count
    
    return {
        "message": "Proxies checked successfully",
        "checked": len(results),
        "active": active_count,
        "inactive": inactive_count
    }

# 代理使用历史记录相关API
@router.post("/usage/history", response_model=ProxyUsageHistoryResponse)
async def create_proxy_usage_history(
    history_data: ProxyUsageHistoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建代理使用历史记录"""
    service = ProxyService(db)
    
    history = await service.create_usage_history(history_data)
    return history

@router.get("/usage/history/{history_id}", response_model=ProxyUsageHistoryResponse)
async def get_proxy_usage_history(
    history_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取代理使用历史记录详情"""
    service = ProxyService(db)
    
    history = await service.get_usage_history(history_id)
    if not history:
        raise HTTPException(status_code=404, detail="Usage history not found")
    
    return history

@router.get("/{proxy_id}/usage/statistics", response_model=Dict)
async def get_proxy_usage_statistics(
    proxy_id: str,
    days: int = Query(7, ge=1, le=365, description="统计天数"),
    db: AsyncSession = Depends(get_db)
):
    """获取代理使用统计信息"""
    service = ProxyService(db)
    
    # 检查代理是否存在
    proxy = await service.get_proxy(proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    
    statistics = await service.get_proxy_usage_statistics(proxy_id, days)
    return statistics

@router.get("/usage/history", response_model=ProxyUsageHistoryListResponse)
async def get_all_usage_history(
    proxy_ip: Optional[str] = None,
    account_email: Optional[str] = None,
    task_name: Optional[str] = None,
    service_name: Optional[str] = None,
    success: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """获取所有代理使用历史记录列表"""
    service = ProxyService(db)
    
    filter_data = ProxyUsageHistoryFilter(
        proxy_ip=proxy_ip,
        account_email=account_email,
        task_name=task_name,
        service_name=service_name,
        success=success,
        start_date=start_date,
        end_date=end_date,
        page=page,
        size=size
    )
    
    histories, total = await service.get_usage_history_list(filter_data)

    # 计算总页数
    pages = (total + size - 1) // size if total > 0 else 0
    
    return ProxyUsageHistoryListResponse(
        total=total,
        items=histories,
        page=page,
        size=size,
        pages=pages
    )