from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from ..models.account import Account
from ..schemas.account import AccountCreate, AccountUpdate
from ..models.login_history import LoginHistory
import uuid
from datetime import datetime
import json
from ..core.logging import logger

class AccountService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.login_service = LoginService()
        self.proxy_client = ProxyClient()

    async def create_account(self, account_data: AccountCreate) -> Account:
        account = Account(
            id=str(uuid.uuid4()),
            username=account_data.username,
            password=account_data.password,
            email=account_data.email,
            email_password=account_data.email_password,
            login_method=account_data.login_method,
            active=False
        )
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def get_accounts(self, skip: int = 0, limit: int = 100, active: Optional[bool] = None) -> List[Account]:
        query = select(Account)
        if active is not None:
            query = query.filter(Account.active == active)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_account(self, account_id: str) -> Optional[Account]:
        result = await self.db.execute(select(Account).filter(Account.id == account_id))
        return result.scalars().first()

    async def update_account(self, account_id: str, account_data: AccountUpdate) -> Optional[Account]:
        update_data = account_data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.now()
        
        await self.db.execute(
            update(Account)
            .where(Account.id == account_id)
            .values(**update_data)
        )
        await self.db.commit()
        
        return await self.get_account(account_id)

    async def delete_account(self, account_id: str) -> bool:
        result = await self.db.execute(
            delete(Account).where(Account.id == account_id)
        )
        await self.db.commit()
        return result.rowcount > 0
        
    def _truncate_error_msg(self, error_msg: str, max_length: int = 500) -> str:
        """Truncate error message to specified length to prevent database errors"""
        if error_msg and len(error_msg) > max_length:
            return error_msg[:max_length-3] + "..."
        return error_msg
        
    async def record_login_history(
        self, 
        account_id: str, 
        proxy_id: Optional[str], 
        status: str, 
        error_msg: Optional[str] = None,
        cookies_count: int = 0,
        response_time: Optional[int] = None
    ) -> LoginHistory:
        """记录登录历史"""
        login_history = LoginHistory(
            account_id=account_id,
            proxy_id=proxy_id,
            status=status,
            error_msg=self._truncate_error_msg(error_msg) if error_msg else None,
            cookies_count=cookies_count,
            response_time=response_time
        )
        self.db.add(login_history)
        await self.db.commit()
        await self.db.refresh(login_history)
        return login_history

    async def login_account(self, account_id: str, proxy_id: Optional[str] = None) -> Optional[Account]:
        """登录账号并获取cookies"""
        start_time = time.time()
        
        # 获取账号信息
        account = await self.get_account(account_id)
        if not account:
            return None
            
        try:
            # 获取代理信息
            if proxy_id:
                proxy = await self.proxy_client.get_proxy(proxy_id)
            else:
                proxy = await self.proxy_client.get_available_proxy()
                
            if not proxy:
                account.error_msg = self._truncate_error_msg("无法获取可用代理")
                await self.db.commit()
                
                # 记录登录历史
                await self.record_login_history(
                    account_id=account_id,
                    proxy_id=None,
                    status="FAILED",
                    error_msg="无法获取可用代理",
                    response_time=int((time.time() - start_time) * 1000)
                )
                
                return account
                
            # 准备账号信息
            account_dict = {
                "username": account.username,
                "password": account.password,
                "email": account.email,
                "email_password": account.email_password
            }
            
            proxy_dict = {
                "type": proxy.get("protocol", "http"),
                "ip": proxy.get("host"),
                "port": proxy.get("port"),
                "username": proxy.get("username"),
                "password": proxy.get("password")
            }
            
            # 根据登录方法选择不同的登录方式
            cookies_dict = {}
            if account.login_method == "TWITTER":
                logger.info(f"使用Twitter方式登录账号: {account.username}")
                cookies_dict = await self.login_service.login_with_twitter(account_dict, proxy_dict)
            elif account.login_method == "GOOGLE":
                logger.info(f"使用Google方式登录账号: {account.username}")
                google_account = {
                    "email": account.email,
                    "email_password": account.email_password
                }
                cookies_dict = await self.login_service.login_with_google(account_dict, google_account, proxy_dict)
            else:
                error_msg = f"不支持的登录方法: {account.login_method}"
                logger.error(error_msg)
                account.error_msg = self._truncate_error_msg(error_msg)
                await self.db.commit()
                
                # 记录登录历史
                await self.record_login_history(
                    account_id=account_id,
                    proxy_id=proxy.get("id"),
                    status="FAILED",
                    error_msg=error_msg,
                    response_time=int((time.time() - start_time) * 1000)
                )
                
                return account
            
            # 计算响应时间（毫秒）
            response_time = int((time.time() - start_time) * 1000)
            
            # 更新账号信息
            if cookies_dict:
                logger.info(f"账号 {account.username} 登录成功，获取到 {len(cookies_dict)} 个cookies")
                account.cookies = cookies_dict
                account.active = True
                account.last_used = datetime.now()
                account.proxy_id = proxy_id or proxy.get("id")
                account.error_msg = None
                
                # 记录登录历史
                await self.record_login_history(
                    account_id=account_id,
                    proxy_id=proxy.get("id"),
                    status="SUCCESS",
                    cookies_count=len(cookies_dict),
                    response_time=response_time
                )
            else:
                error_msg = "登录失败，未获取到cookies"
                logger.error(f"账号 {account.username} {error_msg}")
                account.active = False
                account.error_msg = self._truncate_error_msg(error_msg)
                
                # 记录登录历史
                await self.record_login_history(
                    account_id=account_id,
                    proxy_id=proxy.get("id"),
                    status="FAILED",
                    error_msg=error_msg,
                    response_time=response_time
                )
            
            await self.db.commit()
            await self.db.refresh(account)
            return account
            
        except Exception as e:
            # 计算响应时间（毫秒）
            response_time = int((time.time() - start_time) * 1000)
            
            error_msg = f"登录异常: {str(e)}"
            logger.error(error_msg)
            account.active = False
            account.error_msg = self._truncate_error_msg(error_msg)
            await self.db.commit()
            
            # 记录登录历史
            await self.record_login_history(
                account_id=account_id,
                proxy_id=proxy.get("id") if proxy else None,
                status="FAILED",
                error_msg=error_msg,
                response_time=response_time
            )
            
            await self.db.refresh(account)
            return account
