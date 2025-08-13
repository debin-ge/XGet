from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Optional

from ..db.database import get_db
from ..models.login_history import LoginHistory
from ..schemas.login_history import LoginHistoryResponse, LoginHistoryListResponse

router = APIRouter()

@router.get("/", response_model=LoginHistoryListResponse)
async def get_login_history(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(20, ge=1, le=100, description="每页大小，最大100"),
    account_id: Optional[str] = Query(None, description="按账号ID过滤"),
    status: Optional[str] = Query(None, description="按状态过滤 (SUCCESS, FAILED)"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取登录历史记录（分页）
    
    - **page**: 页码，从1开始
    - **size**: 每页大小，最大100
    - **account_id**: 可选，按账号ID过滤
    - **status**: 可选，按状态过滤 (SUCCESS, FAILED)
    """
    # 计算偏移量
    offset = (page - 1) * size
    
    # 构建基础查询
    query = select(LoginHistory)
    count_query = select(func.count(LoginHistory.id))
    
    # 添加过滤条件
    if account_id:
        query = query.filter(LoginHistory.account_id == account_id)
        count_query = count_query.filter(LoginHistory.account_id == account_id)
    if status:
        query = query.filter(LoginHistory.status == status)
        count_query = count_query.filter(LoginHistory.status == status)
    
    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 按时间倒序排序并分页
    query = query.order_by(LoginHistory.login_time.desc()).offset(offset).limit(size)
    
    result = await db.execute(query)
    histories = result.scalars().all()
    
    return LoginHistoryListResponse.create(histories, total, page, size)

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

@router.get("/account/{account_id}", response_model=LoginHistoryListResponse)
async def get_login_history_by_account(
    account_id: str,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(20, ge=1, le=100, description="每页大小，最大100"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定账号的登录历史记录（分页）
    
    - **account_id**: 账号ID
    - **page**: 页码，从1开始
    - **size**: 每页大小，最大100
    """
    # 计算偏移量
    offset = (page - 1) * size
    
    # 获取总数
    count_result = await db.execute(
        select(func.count(LoginHistory.id)).filter(LoginHistory.account_id == account_id)
    )
    total = count_result.scalar() or 0
    
    # 获取分页数据
    result = await db.execute(
        select(LoginHistory)
        .filter(LoginHistory.account_id == account_id)
        .order_by(LoginHistory.login_time.desc())
        .offset(offset)
        .limit(size)
    )
    histories = result.scalars().all()
    
    return LoginHistoryListResponse.create(histories, total, page, size) 