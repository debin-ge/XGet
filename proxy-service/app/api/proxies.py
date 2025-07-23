from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict

from ..db.database import get_db
from ..schemas.proxy import (
    ProxyCreate, ProxyUpdate, ProxyResponse, 
    ProxyCheck, ProxyCheckResponse, ProxyCheckResult,
    ProxyImport, ProxyImportResponse, ProxyImportResult
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

@router.get("/", response_model=List[ProxyResponse])
async def get_proxies(
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    country: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取代理列表"""
    service = ProxyService(db)
    return await service.get_proxies(skip, limit, status, country)

@router.get("/available", response_model=List[ProxyResponse])
async def get_available_proxies(
    limit: int = 10,
    country: Optional[str] = None,
    max_latency: Optional[int] = None,
    min_success_rate: Optional[float] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取可用代理"""
    service = ProxyService(db)
    return await service.get_available_proxies(limit, country, max_latency, min_success_rate)

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

@router.post("/import", response_model=ProxyImportResponse)
async def import_proxies(
    import_data: ProxyImport,
    db: AsyncSession = Depends(get_db)
):
    """批量导入代理"""
    service = ProxyService(db)
    proxies = await service.import_proxies(import_data.proxies, import_data.check_availability)
    
    active_count = sum(1 for p in proxies if p.status == "ACTIVE")
    inactive_count = len(proxies) - active_count
    
    results = [
        ProxyImportResult(
            id=p.id,
            type=p.type,
            ip=p.ip,
            status=p.status
        ) for p in proxies
    ]
    
    return ProxyImportResponse(
        total=len(import_data.proxies),
        imported=len(proxies),
        active=active_count,
        inactive=inactive_count,
        proxies=results
    )

@router.post("/import/file", response_model=ProxyImportResponse)
async def import_proxies_from_file(
    file: UploadFile = File(...),
    check_availability: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """从文件导入代理
    
    文件格式:
    type|ip|port|username|password|country|city
    SOCKS5|192.168.1.1|1080|user|pass|US|New York
    HTTP|192.168.1.2|8080||||||
    """
    service = ProxyService(db)
    proxies_data = []
    
    content = await file.read()
    text = content.decode('utf-8')
    
    # 支持CSV和自定义格式
    if file.filename.endswith('.csv'):
        reader = csv.reader(io.StringIO(text))
        next(reader, None)  # 跳过标题行
        for row in reader:
            if len(row) >= 3:
                proxy_data = ProxyCreate(
                    type=row[0],
                    ip=row[1],
                    port=int(row[2]),
                    username=row[3] if len(row) > 3 and row[3] else None,
                    password=row[4] if len(row) > 4 and row[4] else None,
                    country=row[5] if len(row) > 5 and row[5] else None,
                    city=row[6] if len(row) > 6 and row[6] else None
                )
                proxies_data.append(proxy_data)
    else:
        # 自定义格式：type|ip|port|username|password|country|city
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            parts = line.split('|')
            if len(parts) >= 3:
                proxy_data = ProxyCreate(
                    type=parts[0],
                    ip=parts[1],
                    port=int(parts[2]),
                    username=parts[3] if len(parts) > 3 and parts[3] else None,
                    password=parts[4] if len(parts) > 4 and parts[4] else None,
                    country=parts[5] if len(parts) > 5 and parts[5] else None,
                    city=parts[6] if len(parts) > 6 and parts[6] else None
                )
                proxies_data.append(proxy_data)
    
    # 导入代理
    proxies = await service.import_proxies(proxies_data, check_availability)
    
    active_count = sum(1 for p in proxies if p.status == "ACTIVE")
    inactive_count = len(proxies) - active_count
    
    results = [
        ProxyImportResult(
            id=p.id,
            type=p.type,
            ip=p.ip,
            status=p.status
        ) for p in proxies
    ]
    
    return ProxyImportResponse(
        total=len(proxies_data),
        imported=len(proxies),
        active=active_count,
        inactive=inactive_count,
        proxies=results
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
    min_success_rate: Optional[float] = 0.8,
    db: AsyncSession = Depends(get_db)
):
    """轮换代理（获取一个可用代理并标记为已使用）"""
    service = ProxyService(db)
    
    # 获取可用代理
    proxies = await service.get_available_proxies(
        limit=1,
        country=country,
        max_latency=max_latency,
        min_success_rate=min_success_rate
    )
    
    if not proxies:
        raise HTTPException(status_code=404, detail="No available proxy found")
    
    proxy = proxies[0]
    
    # 更新代理使用时间
    proxy = await service.update_proxy(
        proxy.id,
        ProxyUpdate(last_used=datetime.now())
    )
    
    return proxy

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