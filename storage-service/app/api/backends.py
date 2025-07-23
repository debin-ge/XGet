from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Path, Body, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.database import get_db
from ..services.backend_service import BackendService
from ..schemas.storage_backend import (
    StorageBackendCreate,
    StorageBackendUpdate,
    StorageBackendResponse,
    StorageBackendList,
)

router = APIRouter()

@router.post("", response_model=StorageBackendResponse, status_code=status.HTTP_201_CREATED)
async def create_storage_backend(
    backend_data: StorageBackendCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    创建新的存储后端
    """
    service = BackendService()
    backend = await service.create_backend(db, backend_data)
    if not backend:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="创建存储后端失败，名称可能已存在或配置无效"
        )
    return backend

@router.get("", response_model=StorageBackendList)
async def get_storage_backends(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: str = Query(None, description="按状态过滤"),
    type: str = Query(None, description="按类型过滤"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取存储后端列表
    """
    service = BackendService()
    backends, total = await service.get_backends(db, skip, limit, status, type)
    return {
        "backends": backends,
        "total": total
    }

@router.get("/{backend_id}", response_model=StorageBackendResponse)
async def get_storage_backend(
    backend_id: str = Path(..., description="存储后端ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取指定ID的存储后端
    """
    service = BackendService()
    backend = await service.get_backend(db, backend_id)
    if not backend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"存储后端未找到: {backend_id}"
        )
    return backend

@router.put("/{backend_id}", response_model=StorageBackendResponse)
async def update_storage_backend(
    backend_id: str = Path(..., description="存储后端ID"),
    backend_data: StorageBackendUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """
    更新存储后端
    """
    service = BackendService()
    backend = await service.update_backend(db, backend_id, backend_data)
    if not backend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"存储后端未找到或更新失败: {backend_id}"
        )
    return backend

@router.delete("/{backend_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_storage_backend(
    backend_id: str = Path(..., description="存储后端ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    删除存储后端
    """
    service = BackendService()
    success = await service.delete_backend(db, backend_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"存储后端未找到或无法删除（可能有存储项正在使用）: {backend_id}"
        )

@router.post("/{backend_id}/test", response_model=Dict[str, Any])
async def test_storage_backend(
    backend_id: str = Path(..., description="存储后端ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    测试存储后端连接
    """
    service = BackendService()
    result = await service.test_backend(db, backend_id)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    return result 