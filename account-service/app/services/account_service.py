from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, func
from ..models.account import Account
from ..schemas.account import AccountCreate, AccountUpdate, AccountListResponse
from ..models.login_history import LoginHistory
import uuid
import time
from datetime import datetime
from ..core.logging import logger
from ..core.cache import cache
from ..core.redis import RedisManager
from .login_service import LoginService
from .proxy_client import ProxyClient

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

    @cache(prefix="accounts_paginated", expire=120)  # 2分钟缓存
    async def get_accounts_paginated(self, page: int = 1, size: int = 20, active: Optional[bool] = None, login_method: Optional[str] = None, search: Optional[str] = None) -> AccountListResponse:
        """获取分页的账户列表"""
        
        # 计算偏移量
        offset = (page - 1) * size
        
        # 构建基础查询
        query = select(Account)
        count_query = select(func.count(Account.id))
        
        query = query.filter(Account.is_deleted == False)
        count_query = count_query.filter(Account.is_deleted == False)
        
        # 添加筛选条件
        if active is not None:
            query = query.filter(Account.active == active)
            count_query = count_query.filter(Account.active == active)
        
        if login_method is not None:
            query = query.filter(Account.login_method == login_method.upper())
            count_query = count_query.filter(Account.login_method == login_method.upper())
        
        if search is not None:
            query = query.filter(Account.username.ilike(f"%{search}%") | Account.email.ilike(f"%{search}%"))
            count_query = count_query.filter(Account.username.ilike(f"%{search}%") | Account.email.ilike(f"%{search}%"))
        
        # 执行查询
        query = query.offset(offset).limit(size).order_by(Account.created_at.desc())
        
        accounts_result = await self.db.execute(query)
        accounts = accounts_result.scalars().all()
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # 构建响应
        response = AccountListResponse.create(accounts, total, page, size)
        
        return response

    @cache(prefix="account", expire=300)  # 5分钟缓存
    async def get_account(self, account_id: str, include_deleted: bool = False) -> Optional[Account]:
        """获取单个账户，默认不包括已删除的账户""" 
        query = select(Account).filter(Account.id == account_id)
        
        if not include_deleted:
            query = query.filter(Account.is_deleted == False)
            
        result = await self.db.execute(query)
        account = result.scalars().first()
            
        return account

    async def update_account(self, account_id: str, account_data: AccountUpdate) -> Optional[Account]:

        account = await self.get_account(account_id, include_deleted=False)
        if not account:
            return None
            
        update_data = account_data.dict(exclude_unset=True)
        
        if not update_data.get("password"):
            update_data.pop("password")
        if not update_data.get("email_password"):
            update_data.pop("email_password")

        update_data["updated_at"] = datetime.now()
        
        await self.db.execute(
            update(Account)
            .where(Account.id == account_id)
            .where(Account.is_deleted == False)
            .values(**update_data)
        )
        await self.db.commit()
        
        # 使该账户的缓存失效
        await self.invalidate_account_cache(account_id)
        
        return await self.get_account(account_id)

    async def delete_account(self, account_id: str) -> bool:
        """软删除账户"""

        account = await self.get_account(account_id, include_deleted=False)
        if not account:
            return False
            

        result = await self.db.execute(
            update(Account)
            .where(Account.id == account_id)
            .where(Account.is_deleted == False)
            .values(
                is_deleted=True,
                deleted_at=datetime.now(),
                updated_at=datetime.now()
            )
        )
        await self.db.commit()
        
        if result.rowcount > 0:
            logger.info(f"成功软删除账户: {account_id}")
            # 使该账户的缓存失效
            await self.invalidate_account_cache(account_id)
            return True
        else:
            logger.warning(f"软删除账户失败: {account_id}")
            return False
   
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
        response_time: Optional[int] = None
    ) -> LoginHistory:
        """记录登录历史"""
        login_history = LoginHistory(
            account_id=account_id,
            proxy_id=proxy_id,
            status=status,
            error_msg=self._truncate_error_msg(error_msg) if error_msg else None,
            response_time=response_time
        )
        self.db.add(login_history)
        await self.db.commit()
        await self.db.refresh(login_history)
        return login_history

    async def login_account(self, account_id: str, proxy_id: Optional[str] = None) -> Optional[Account]:
        """登录账号并获取cookies"""
        start_time = time.time()
        error_msg = ""
        status = ""
        
        # 获取账号信息
        account = await self.get_account(account_id)
        if not account:
            return None
            
        try:
            # 获取代理信息
            if proxy_id:
                proxy = await self.proxy_client.get_proxy(proxy_id)
            else:
                proxy = await self.proxy_client.get_rotating_proxy()
                
            if not proxy:
                account.error_msg = self._truncate_error_msg("无法获取可用代理")
                error_msg = "无法获取可用代理"
                status = "FAILED"

                return account
            
            # 根据登录方法选择不同的登录方式
            cookies_dict = {}
            if account.login_method == "TWITTER":
                logger.info(f"使用Twitter方式登录账号: {account.username}")
                cookies_dict = await self.login_service.login_with_twitter(account, proxy)
            elif account.login_method == "GOOGLE":
                logger.info(f"使用Google方式登录账号: {account.email}")

                cookies_dict = await self.login_service.login_with_google(account, proxy)
            else:
                error_msg = f"不支持的登录方法: {account.login_method}"
                logger.error(error_msg)
                account.error_msg = self._truncate_error_msg(error_msg)
                status = "FAILED"

                return account
            
            # 更新账号信息
            if cookies_dict:
                logger.info(f"账号 {account.username} 登录成功，获取到 {len(cookies_dict)} 个cookies")
                account.cookies = cookies_dict
                account.active = True
                account.last_used = datetime.now()
                account.proxy_id = proxy_id or proxy.id
                account.error_msg = None

                status = "SUCCESS"
                
                # 缓存登录成功的账号信息（24小时）
                cache_key = f"account:login_success:{account.id}"
                await RedisManager.set_json(cache_key, {
                    "id": account.id,
                    "username": account.username,
                    "email": account.email,
                    "login_method": account.login_method,
                    "cookies": account.cookies,
                    "active": account.active,
                    "last_used": account.last_used.isoformat() if account.last_used else None,
                    "proxy_id": account.proxy_id
                }, expire=86400)  # 24小时缓存
            else:
                error_msg = "登录失败，未获取到cookies"
                logger.error(f"账号 {account.username} {error_msg}")
                account.active = False
                account.error_msg = self._truncate_error_msg(error_msg)
                status = "FAILED"
            
            return account
            
        except Exception as e:
            error_msg = f"登录异常: {str(e)}"
            logger.error(error_msg)
            account.active = False
            account.error_msg = self._truncate_error_msg(error_msg)
            
            
            await self.db.refresh(account)
            return account

        finally:
            # 记录登录历史
            await self.record_login_history(
                account_id=account_id,
                proxy_id=proxy.id if proxy else None,
                status=status,
                error_msg=error_msg,
                response_time=int((time.time() - start_time) * 1000)
            )

            await self.db.commit()
            await self.db.refresh(account)

    async def invalidate_account_cache(self, account_id: str) -> int:
        """
        使指定账户的缓存失效
        :param account_id: 账户ID
        :return: 删除的缓存键数量
        """
        # 删除账户相关的所有缓存
        patterns = [
            f"account:*{account_id}*",
            f"accounts_paginated:*",  # 分页缓存也需要失效
            f"account:login_success:{account_id}"
        ]
        
        deleted_count = 0
        for pattern in patterns:
            deleted_count += await RedisManager.delete_keys(pattern)
        
        logger.info(f"已失效账户 {account_id} 的 {deleted_count} 个缓存键")
        return deleted_count
