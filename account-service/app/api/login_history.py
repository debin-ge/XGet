from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from ..db.database import get_db
from ..models.login_history import LoginHistory
from ..schemas.login_history import LoginHistoryResponse

router = APIRouter()

@router.get("/", response_model=List[LoginHistoryResponse])
async def get_login_history(
    skip: int = 0, 
    limit: int = 100,
    account_id: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取登录历史记录
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数
    - **account_id**: 可选，按账号ID过滤
    - **status**: 可选，按状态过滤 (SUCCESS, FAILED)
    """
    query = select(LoginHistory)
    
    # 添加过滤条件
    if account_id:
        query = query.filter(LoginHistory.account_id == account_id)
    if status:
        query = query.filter(LoginHistory.status == status)
    
    # 按时间倒序排序
    query = query.order_by(LoginHistory.login_time.desc())
    
    # 分页
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{history_id}", response_model=LoginHistoryResponse)
async def get_login_history_by_id(
    history_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    根据ID获取登录历史记录
    
    - **history_id**: 登录历史记录ID
    """
    result = await db.execute(
        select(LoginHistory).filter(LoginHistory.id == history_id)
    )
    history = result.scalars().first()
    
    if not history:
        raise HTTPException(status_code=404, detail="Login history not found")
    
    return history

@router.get("/account/{account_id}", response_model=List[LoginHistoryResponse])
async def get_login_history_by_account(
    account_id: str,
    skip: int = 0, 
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定账号的登录历史记录
    
    - **account_id**: 账号ID
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数
    """
    result = await db.execute(
        select(LoginHistory)
        .filter(LoginHistory.account_id == account_id)
        .order_by(LoginHistory.login_time.desc())
        .offset(skip)
        .limit(limit)
    )
    
    return result.scalars().all() 