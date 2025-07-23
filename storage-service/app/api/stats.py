from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.database import get_db
from ..services.storage_service import StorageService
from ..storage.factory import StorageBackendFactory

router = APIRouter()

@router.get("", response_model=Dict[str, Any])
async def get_storage_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    获取存储统计信息
    """
    service = StorageService()
    stats = await service.get_stats(db)
    return stats

@router.get("/backend/{backend_id}", response_model=Dict[str, Any])
async def get_backend_stats(
    backend_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    获取指定存储后端的统计信息
    """
    try:
        # 获取后端实例
        backend = await StorageBackendFactory.get_backend(backend_id)
        if not backend:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"存储后端未找到: {backend_id}"
            )
        
        # 获取后端统计信息
        stats = await backend.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取后端统计信息失败: {str(e)}"
        )

@router.get("/health", response_model=Dict[str, Any])
async def get_health_status(
    db: AsyncSession = Depends(get_db),
):
    """
    获取存储服务健康状态
    """
    try:
        # 检查数据库连接
        db_status = "healthy"
        db_message = "数据库连接正常"
        
        # 检查MongoDB连接
        from ..db.database import mongo_db
        mongodb_status = "healthy" if mongo_db else "unhealthy"
        mongodb_message = "MongoDB连接正常" if mongo_db else "MongoDB连接失败"
        
        # 检查MinIO连接
        from ..db.database import minio_client
        minio_status = "healthy" if minio_client else "unhealthy"
        minio_message = "MinIO连接正常" if minio_client else "MinIO连接失败"
        
        # 检查Elasticsearch连接
        from ..db.database import es_client
        es_status = "healthy" if es_client else "unhealthy"
        es_message = "Elasticsearch连接正常" if es_client else "Elasticsearch连接失败"
        
        # 获取后端状态
        backend_statuses = {}
        try:
            # 获取默认S3后端
            s3_backend = await StorageBackendFactory.get_backend("S3")
            if s3_backend:
                s3_health = await s3_backend.health_check()
                backend_statuses["S3"] = s3_health
            
            # 获取默认MongoDB后端
            mongodb_backend = await StorageBackendFactory.get_backend("MONGODB")
            if mongodb_backend:
                mongodb_health = await mongodb_backend.health_check()
                backend_statuses["MONGODB"] = mongodb_health
        except Exception as e:
            backend_statuses["error"] = str(e)
        
        # 总体状态
        overall_status = "healthy"
        if (db_status != "healthy" or mongodb_status != "healthy" or
            minio_status != "healthy" or es_status != "healthy"):
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "database": {
                    "status": db_status,
                    "message": db_message
                },
                "mongodb": {
                    "status": mongodb_status,
                    "message": mongodb_message
                },
                "minio": {
                    "status": minio_status,
                    "message": minio_message
                },
                "elasticsearch": {
                    "status": es_status,
                    "message": es_message
                }
            },
            "backends": backend_statuses
        }
    except Exception as e:
        from datetime import datetime
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        } 