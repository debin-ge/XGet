from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from ..db.database import get_db
from ..schemas.account import AccountCreate, AccountUpdate, AccountResponse, AccountLogin, AccountLoginResponse, AccountListResponse
from ..services.account_service import AccountService

router = APIRouter()

@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account: AccountCreate, 
    db: AsyncSession = Depends(get_db)
):
    service = AccountService(db)
    return await service.create_account(account)

@router.get("/", response_model=AccountListResponse)
async def get_accounts(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(20, ge=1, le=100, description="每页大小，最大100"),
    active: Optional[bool] = Query(None, description="按激活状态筛选"),
    login_method: Optional[str] = Query(None, description="按登录方式筛选"),
    search: Optional[str] = Query(None, description="按用户名或邮箱搜索"),
    db: AsyncSession = Depends(get_db)
):
    """获取账户列表（分页）"""
    service = AccountService(db)
    return await service.get_accounts_paginated(page, size, active, login_method, search)


@router.post("/login", response_model=AccountLoginResponse)
async def login_account(
    login_data: AccountLogin,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    登录账号，可以指定代理或使用系统自动选择的代理
    
    - **account_id**: 账号ID
    - **proxy_id**: 可选的代理ID，如果不提供则自动选择一个可用代理
    
    登录过程可能需要一些时间，因此默认会在后台执行。
    返回的状态表示登录是否成功启动，而不是登录是否成功完成。
    """
    service = AccountService(db)
    
    # 先检查账号是否存在
    account = await service.get_account(login_data.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # 异步执行登录
    if login_data.async_login:
        # 在后台任务中执行登录
        background_tasks.add_task(service.login_account, login_data.account_id, login_data.proxy_id)
        
        # 返回立即响应
        return AccountLoginResponse(
            id=account.id,
            username=account.username,
            active=account.active,
            login_successful=True,  # 表示登录过程已启动
            cookies_obtained=False,  # 实际结果需要稍后检查
            last_used=account.last_used or datetime.now(),
            message="登录过程已在后台启动，请稍后检查账号状态"
        )
    else:
        # 同步执行登录
        updated_account = await service.login_account(login_data.account_id, login_data.proxy_id)
        
        # 返回登录结果
        return AccountLoginResponse(
            id=updated_account.id,
            username=updated_account.username,
            active=updated_account.active,
            login_successful=updated_account.active,
            cookies_obtained=updated_account.cookies is not None and len(updated_account.cookies) > 0,
            last_used=updated_account.last_used,
            message=updated_account.error_msg if updated_account.error_msg else "登录成功" if updated_account.active else "登录失败"
        )

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str, 
    include_deleted: bool = Query(False, description="是否包括已删除的账户"),
    db: AsyncSession = Depends(get_db)
):
    service = AccountService(db)
    account = await service.get_account(account_id, include_deleted)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str, 
    account_data: AccountUpdate, 
    db: AsyncSession = Depends(get_db)
):
    service = AccountService(db)
    account = await service.update_account(account_id, account_data)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.delete("/{account_id}", response_model=dict)
async def delete_account(
    account_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """软删除账户"""
    service = AccountService(db)
    success = await service.delete_account(account_id)
    if not success:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"message": "Account deleted successfully"}
