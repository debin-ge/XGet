from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Path, Body, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.database import get_db
from ..services.storage_service import StorageService
from ..schemas.metadata import MetadataUpdate, MetadataResponse

router = APIRouter()

@router.get("/{item_id}/metadata", response_model=Dict[str, Any])
async def get_metadata(
    item_id: str = Path(..., description="存储项ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取存储项元数据
    """
    service = StorageService()
    item = await service.get_item(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"存储项未找到: {item_id}"
        )
    
    return item.get("metadata", {})

@router.put("/{item_id}/metadata", response_model=Dict[str, Any])
async def update_metadata(
    item_id: str = Path(..., description="存储项ID"),
    metadata_update: MetadataUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """
    更新存储项元数据
    """
    service = StorageService()
    result = await service.update_item(db, item_id, None, metadata_update)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"存储项未找到: {item_id}"
        )
    
    return result.get("metadata", {})

@router.get("/tags", response_model=List[str])
async def get_all_tags(
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """
    获取所有标签列表
    """
    # 这里可以实现获取所有标签的逻辑
    # 暂时返回空列表，可以根据需要扩展
    return []

@router.get("/search/by-tag", response_model=Dict[str, Any])
async def search_by_tag(
    tag: str = Query(..., description="标签"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    按标签搜索存储项
    """
    service = StorageService()
    items, total = await service.search_items(
        db, tags=[tag], limit=limit, offset=offset
    )
    
    return {
        "tag": tag,
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/search/by-source", response_model=Dict[str, Any])
async def search_by_source(
    source_id: str = Query(..., description="源ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    按源ID搜索存储项
    """
    service = StorageService()
    items, total = await service.search_items(
        db, source_id=source_id, limit=limit, offset=offset
    )
    
    return {
        "source_id": source_id,
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    } 