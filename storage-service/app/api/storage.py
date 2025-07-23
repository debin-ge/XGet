from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.database import get_db
from ..services.storage_service import StorageService
from ..schemas.storage import (
    StorageRequest,
    BatchStorageRequest,
    StorageResponse,
    StorageSearchRequest,
    StorageSearchResponse,
    StorageStatsResponse,
)

router = APIRouter()

@router.post("", response_model=StorageResponse, status_code=status.HTTP_201_CREATED)
async def store_data(
    storage_request: StorageRequest,
    backend: str = Query("S3", description="存储后端类型"),
    db: AsyncSession = Depends(get_db),
):
    """
    存储数据到指定后端
    """
    service = StorageService()
    try:
        result = await service.store_data(db, storage_request, backend)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"存储数据失败: {str(e)}"
        )

@router.post("/batch", response_model=List[StorageResponse], status_code=status.HTTP_201_CREATED)
async def store_batch_data(
    batch_request: BatchStorageRequest,
    backend: str = Query("S3", description="存储后端类型"),
    db: AsyncSession = Depends(get_db),
):
    """
    批量存储数据到指定后端
    """
    service = StorageService()
    try:
        results = await service.store_batch(db, batch_request, backend)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量存储数据失败: {str(e)}"
        )

@router.get("/{item_id}", response_model=StorageResponse)
async def get_storage_item(
    item_id: str = Path(..., description="存储项ID"),
    include_data: bool = Query(False, description="是否包含数据内容"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取存储项信息
    """
    service = StorageService()
    item = await service.get_item(db, item_id, include_data)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"存储项未找到: {item_id}"
        )
    return item

@router.get("", response_model=StorageSearchResponse)
async def search_storage_items(
    query: Optional[str] = None,
    data_type: Optional[str] = None,
    source_id: Optional[str] = None,
    processing_id: Optional[str] = None,
    status: Optional[str] = None,
    tags: Optional[List[str]] = Query(None, description="标签列表"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序顺序"),
    db: AsyncSession = Depends(get_db),
):
    """
    搜索存储项
    """
    service = StorageService()
    items, total = await service.search_items(
        db, query, data_type, tags, source_id, processing_id, status,
        start_date, end_date, limit, offset, sort_by, sort_order
    )
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.post("/search", response_model=StorageSearchResponse)
async def advanced_search(
    search_request: StorageSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    高级搜索（支持复杂查询条件）
    """
    # 这里可以实现更复杂的搜索逻辑
    # 暂时简单实现，可以根据需要扩展
    service = StorageService()
    items, total = await service.search_items(
        db, limit=search_request.limit, offset=search_request.offset
    )
    return {
        "items": items,
        "total": total,
        "limit": search_request.limit,
        "offset": search_request.offset
    }

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_storage_item(
    item_id: str = Path(..., description="存储项ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    删除存储项
    """
    service = StorageService()
    success = await service.delete_item(db, item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"存储项未找到或删除失败: {item_id}"
        )

@router.get("/stats", response_model=StorageStatsResponse)
async def get_storage_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    获取存储统计信息
    """
    service = StorageService()
    stats = await service.get_stats(db)
    return stats 