from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Path, Body, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.database import get_db
from ..services.policy_service import PolicyService
from ..schemas.retention_policy import (
    RetentionPolicyCreate,
    RetentionPolicyUpdate,
    RetentionPolicyResponse,
    RetentionPolicyList,
)

router = APIRouter()

@router.post("", response_model=RetentionPolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_retention_policy(
    policy_data: RetentionPolicyCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    创建新的保留策略
    """
    service = PolicyService()
    policy = await service.create_policy(db, policy_data)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="创建保留策略失败，名称可能已存在或参数无效"
        )
    return policy

@router.get("", response_model=RetentionPolicyList)
async def get_retention_policies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    获取保留策略列表
    """
    service = PolicyService()
    policies, total = await service.get_policies(db, skip, limit)
    return {
        "policies": policies,
        "total": total
    }

@router.get("/{policy_id}", response_model=RetentionPolicyResponse)
async def get_retention_policy(
    policy_id: str = Path(..., description="保留策略ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取指定ID的保留策略
    """
    service = PolicyService()
    policy = await service.get_policy(db, policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"保留策略未找到: {policy_id}"
        )
    return policy

@router.put("/{policy_id}", response_model=RetentionPolicyResponse)
async def update_retention_policy(
    policy_id: str = Path(..., description="保留策略ID"),
    policy_data: RetentionPolicyUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """
    更新保留策略
    """
    service = PolicyService()
    policy = await service.update_policy(db, policy_id, policy_data)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"保留策略未找到或更新失败: {policy_id}"
        )
    return policy

@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_retention_policy(
    policy_id: str = Path(..., description="保留策略ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    删除保留策略
    """
    service = PolicyService()
    success = await service.delete_policy(db, policy_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"保留策略未找到或无法删除（可能有存储项正在使用）: {policy_id}"
        ) 