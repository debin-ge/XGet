from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Path, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.database import get_db
from ..services.storage_service import StorageService
from ..schemas.lifecycle import LifecycleInfo, LifecycleUpdate, LifecycleResponse

router = APIRouter()

@router.get("/{item_id}", response_model=Dict[str, Any])
async def get_lifecycle_info(
    item_id: str = Path(..., description="存储项ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取存储项生命周期信息
    """
    service = StorageService()
    lifecycle_info = await service.get_lifecycle_info(db, item_id)
    if not lifecycle_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"存储项未找到: {item_id}"
        )
    return lifecycle_info

@router.put("/{item_id}", response_model=LifecycleResponse)
async def update_lifecycle(
    item_id: str = Path(..., description="存储项ID"),
    lifecycle_update: LifecycleUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """
    更新存储项生命周期策略
    """
    service = StorageService()
    result = await service.update_lifecycle(db, item_id, lifecycle_update.retention_policy)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"存储项未找到: {item_id}"
        )
    
    if not result.get("applied", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "更新生命周期策略失败")
        )
    
    return result

@router.post("/process", response_model=Dict[str, Any])
async def process_lifecycle_tasks(
    db: AsyncSession = Depends(get_db),
):
    """
    处理生命周期任务（归档和删除）
    
    此端点应通过定时任务调用，或由管理员手动触发
    """
    service = StorageService()
    result = await service.process_lifecycle_tasks(db)
    
    if result.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "处理生命周期任务失败")
        )
    
    return result 