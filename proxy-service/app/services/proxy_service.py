from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, desc, asc, or_, and_
from ..models.proxy import Proxy
from ..schemas.proxy import ProxyCreate, ProxyUpdate, ProxyCheckResult
from ..core.logging import logger
import uuid
from datetime import datetime, timedelta
import aiohttp
import asyncio


class ProxyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_proxy(self, proxy_data: ProxyCreate) -> Proxy:
        """创建代理"""
        proxy = Proxy(
            id=str(uuid.uuid4()),
            type=proxy_data.type,
            ip=proxy_data.ip,
            port=proxy_data.port,
            username=proxy_data.username,
            password=proxy_data.password,
            country=proxy_data.country,
            city=proxy_data.city,
            status="INACTIVE",
            success_rate=0.0
        )
        self.db.add(proxy)
        await self.db.commit()
        await self.db.refresh(proxy)
        
        logger.info(f"创建代理成功, proxy_id: {proxy.id}, ip: {proxy.ip}, port: {proxy.port}, type: {proxy.type}")
        return proxy

    async def get_proxies(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        status: Optional[str] = None,
        country: Optional[str] = None
    ) -> List[Proxy]:
        """获取代理列表"""
        query = select(Proxy)
        if status:
            query = query.filter(Proxy.status == status)
        if country:
            query = query.filter(Proxy.country == country)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        proxies = result.scalars().all()
        
        logger.debug(f"获取代理列表, count: {len(proxies)}, status: {status}, country: {country}")
        return proxies

    async def get_proxy(self, proxy_id: str) -> Optional[Proxy]:
        """获取代理详情"""
        result = await self.db.execute(select(Proxy).filter(Proxy.id == proxy_id))
        proxy = result.scalars().first()
        
        if proxy:
            logger.debug(f"获取代理详情成功, proxy_id: {proxy_id}")
        else:
            logger.debug(f"代理不存在, proxy_id: {proxy_id}")
        
        return proxy

    async def update_proxy(self, proxy_id: str, proxy_data: ProxyUpdate) -> Optional[Proxy]:
        """更新代理信息"""
        update_data = proxy_data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.now()
        
        await self.db.execute(
            update(Proxy)
            .where(Proxy.id == proxy_id)
            .values(**update_data)
        )
        await self.db.commit()
        
        proxy = await self.get_proxy(proxy_id)
        if proxy:
            logger.info(f"更新代理成功, proxy_id: {proxy_id}, fields: {list(update_data.keys())}")
        else:
            logger.error(f"更新代理失败，代理不存在, proxy_id: {proxy_id}")
        
        return proxy

    async def delete_proxy(self, proxy_id: str) -> bool:
        """删除代理"""
        result = await self.db.execute(
            delete(Proxy).where(Proxy.id == proxy_id)
        )
        await self.db.commit()
        
        success = result.rowcount > 0
        if success:
            logger.info(f"删除代理成功, proxy_id: {proxy_id}")
        else:
            logger.error(f"删除代理失败，代理不存在, proxy_id: {proxy_id}")
        
        return success

    async def get_available_proxies(
        self,
        limit: int = 10,
        country: Optional[str] = None,
        max_latency: Optional[int] = None,
        min_success_rate: Optional[float] = None
    ) -> List[Proxy]:
        """获取可用代理"""
        query = select(Proxy).filter(Proxy.status == "ACTIVE")
        
        if country:
            query = query.filter(Proxy.country == country)
        if max_latency:
            query = query.filter(Proxy.latency <= max_latency)
        if min_success_rate:
            query = query.filter(Proxy.success_rate >= min_success_rate)
            
        query = query.order_by(Proxy.latency).limit(limit)
        result = await self.db.execute(query)
        proxies = result.scalars().all()
        
        logger.debug(f"获取可用代理, count: {len(proxies)}, country: {country}, max_latency: {max_latency}, min_success_rate: {min_success_rate}")
        
        return proxies

    async def check_proxy(self, proxy: Proxy) -> ProxyCheckResult:
        """检查代理可用性"""
        result = ProxyCheckResult(
            id=proxy.id,
            status="INACTIVE",
            latency=None,
            success_rate=proxy.success_rate,
            error_msg=None
        )
        
        try:
            # 更新代理状态为检查中
            proxy.status = "CHECKING"
            await self.db.commit()
            
            proxy_url = None
            if proxy.username and proxy.password:
                proxy_url = f"{proxy.type.lower()}://{proxy.username}:{proxy.password}@{proxy.ip}:{proxy.port}"
            else:
                proxy_url = f"{proxy.type.lower()}://{proxy.ip}:{proxy.port}"
                
            logger.debug(f"开始检查代理, proxy_id: {proxy.id}, proxy_url: {proxy_url}")
                
            start_time = datetime.now()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://httpbin.org/ip', 
                    proxy=proxy_url, 
                    timeout=10
                ) as response:
                    if response.status == 200:
                        end_time = datetime.now()
                        latency = int((end_time - start_time).total_seconds() * 1000)
                        
                        # 更新代理信息
                        proxy.status = "ACTIVE"
                        proxy.latency = latency
                        proxy.last_check = datetime.now()
                        
                        # 更新成功率
                        if proxy.success_rate == 0:
                            proxy.success_rate = 1.0
                        else:
                            proxy.success_rate = 0.8 * proxy.success_rate + 0.2 * 1.0
                            
                        await self.db.commit()
                        
                        result.status = "ACTIVE"
                        result.latency = latency
                        result.success_rate = proxy.success_rate
                        
                        logger.info(f"代理检查成功, proxy_id: {proxy.id}, latency: {latency}, success_rate: {proxy.success_rate}")
                    else:
                        # 更新代理信息
                        proxy.status = "INACTIVE"
                        proxy.last_check = datetime.now()
                        
                        # 更新成功率
                        if proxy.success_rate > 0:
                            proxy.success_rate = 0.8 * proxy.success_rate
                            
                        await self.db.commit()
                        
                        result.error_msg = f"HTTP status: {response.status}"
                        
                        logger.error(f"代理检查失败, proxy_id: {proxy.id}, http_status: {response.status}, success_rate: {proxy.success_rate}")
        except Exception as e:
            # 更新代理信息
            proxy.status = "INACTIVE"
            proxy.last_check = datetime.now()
            
            # 更新成功率
            if proxy.success_rate > 0:
                proxy.success_rate = 0.8 * proxy.success_rate
                
            await self.db.commit()
            
            result.error_msg = str(e)
            
            logger.error(f"代理检查异常, proxy_id: {proxy.id}, error: {str(e)}, success_rate: {proxy.success_rate}")
            
        return result

    async def check_proxies(self, proxy_ids: List[str]) -> List[ProxyCheckResult]:
        """批量检查代理可用性"""
        results = []
        
        logger.info(f"开始批量检查代理, count: {len(proxy_ids)}")
        
        for proxy_id in proxy_ids:
            proxy = await self.get_proxy(proxy_id)
            if proxy:
                result = await self.check_proxy(proxy)
                results.append(result)
            else:
                results.append(ProxyCheckResult(
                    id=proxy_id,
                    status="INACTIVE",
                    error_msg="Proxy not found"
                ))
                logger.error(f"代理不存在, proxy_id: {proxy_id}")
        
        logger.info(f"批量检查代理完成, total: {len(proxy_ids)}, active: {sum(1 for r in results if r.status == 'ACTIVE')}, inactive: {sum(1 for r in results if r.status == 'INACTIVE')}")
                
        return results

    async def import_proxies(self, proxies_data: List[ProxyCreate], check_availability: bool = True) -> List[Proxy]:
        """批量导入代理"""
        proxies = []
        
        logger.info(f"开始批量导入代理, count: {len(proxies_data)}")
        
        for proxy_data in proxies_data:
            proxy = await self.create_proxy(proxy_data)
            proxies.append(proxy)
            
        if check_availability:
            # 异步检查所有代理可用性
            proxy_ids = [proxy.id for proxy in proxies]
            logger.info(f"检查导入代理可用性, count: {len(proxy_ids)}")
            await self.check_proxies(proxy_ids)
            
            # 重新获取代理信息
            proxies = []
            for proxy_id in proxy_ids:
                proxy = await self.get_proxy(proxy_id)
                if proxy:
                    proxies.append(proxy)
        
        logger.info(f"批量导入代理完成, count: {len(proxies)}")
                    
        return proxies

    async def get_proxies_for_check(self, limit: int = 100) -> List[Proxy]:
        """获取需要检查的代理"""
        now = datetime.now()
        
        # 1. 状态为ACTIVE但最后检查时间超过30分钟的代理
        active_check_time = now - timedelta(minutes=30)
        # 2. 状态为INACTIVE但最后检查时间超过2小时的代理
        inactive_check_time = now - timedelta(hours=2)
        # 3. 状态为CHECKING但最后检查时间超过10分钟的代理（可能是上次检查异常）
        checking_check_time = now - timedelta(minutes=10)
        
        query = select(Proxy).where(
            or_(
                and_(
                    Proxy.status == "ACTIVE",
                    or_(
                        Proxy.last_check == None,
                        Proxy.last_check < active_check_time
                    )
                ),
                and_(
                    Proxy.status == "INACTIVE",
                    or_(
                        Proxy.last_check == None,
                        Proxy.last_check < inactive_check_time
                    )
                ),
                and_(
                    Proxy.status == "CHECKING",
                    or_(
                        Proxy.last_check == None,
                        Proxy.last_check < checking_check_time
                    )
                )
            )
        ).order_by(
            asc(Proxy.last_check)
        ).limit(limit)
        
        result = await self.db.execute(query)
        proxies = result.scalars().all()
        
        logger.debug(f"获取需要检查的代理, count: {len(proxies)}")
        
        return proxies