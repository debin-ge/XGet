from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, desc, asc, or_, and_, func, exists
from ..models.proxy import Proxy, ProxyQuality, ProxyUsageHistory
from ..schemas.proxy import (
    ProxyCreate, ProxyUpdate, ProxyCheckResult, ProxyQualityCreate, ProxyQualityUpdate,
    ProxyUsageHistoryCreate, ProxyUsageHistoryFilter, ProxyListResponse, ProxyUsageHistoryResponse
)
from ..core.logging import logger
from .ip_geolocation_service import ip_geolocation_service
from .account_client import AccountClient
from .scraper_client import ScraperClient
import uuid
from datetime import datetime, timedelta
import aiohttp
import random

class ProxyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_client = AccountClient()
        self.scraper_client = ScraperClient()

    def _normalize_datetime(self, dt: Optional[datetime]) -> Optional[datetime]:
        """标准化日期时间，移除时区信息以兼容数据库"""
        if dt is None:
            return None
        if dt.tzinfo is not None:
            # 如果有时区信息，移除时区（保持UTC时间）
            return dt.replace(tzinfo=None)
        return dt

    def _build_quality_score_filter(self, min_quality_score: float = 0.0, default_quality_score: float = 0.8):
        """构建质量分数筛选条件的辅助方法
        
        Args:
            min_quality_score: 最小质量分数参数
            default_quality_score: 默认质量分数（对于没有质量记录的代理）
            
        Returns:
            tuple: (score_min, score_max, quality_conditions)
        """
        # 根据传入的min_quality_score确定筛选区间
        if min_quality_score == 0.9:
            # 筛选区间：0.9-1.0
            score_min, score_max = 0.9, 1.0
        elif min_quality_score == 0.7:
            # 筛选区间：0.7-0.9
            score_min, score_max = 0.7, 0.9
        elif min_quality_score == 0.5:
            # 筛选区间：0.5-0.7
            score_min, score_max = 0.5, 0.7
        elif min_quality_score == 0:
            # 筛选区间：0-0.5
            score_min, score_max = 0.0, 0.5
        else:
            score_min, score_max = min_quality_score, 1.0
        
        # 构建筛选条件
        quality_conditions = []

        quality_conditions.append(ProxyQuality.quality_score.between(score_min, score_max))
        
        # 没有质量记录且默认分数在指定区间
        if score_min <= default_quality_score < score_max:
            quality_conditions.append(ProxyQuality.proxy_id.is_(None))
        
        return quality_conditions

    async def create_proxy(self, proxy_data: ProxyCreate) -> Proxy:
        """创建代理"""
        # 根据IP地址获取国家、城市和ISP信息
        try:
            country, city, isp = await ip_geolocation_service.get_ip_info(proxy_data.ip)
            logger.info(f"获取IP地理位置信息成功 - IP: {proxy_data.ip}, Country: {country}, City: {city}, ISP: {isp}")
        except Exception as e:
            logger.warning(f"获取IP地理位置信息失败 - IP: {proxy_data.ip}, Error: {str(e)}")
            country, city, isp = None, None, None

        proxy = Proxy(
            id=str(uuid.uuid4()),
            type=proxy_data.type,
            ip=proxy_data.ip,
            port=proxy_data.port,
            username=proxy_data.username,
            password=proxy_data.password,
            status="INACTIVE",
            success_rate=0.0,
            country=country,
            city=city,
            isp=isp
        )
        self.db.add(proxy)
        await self.db.commit()
        await self.db.refresh(proxy)
        
        # 创建默认的质量记录
        quality = ProxyQuality(
            proxy_id=proxy.id,
            total_usage=0,
            success_count=0,
            quality_score=0.8,  # 初始质量为80%
            cooldown_time=0
        )
        self.db.add(quality)
        await self.db.commit()
        
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

    async def get_proxies_paginated(
        self,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None,
        country: Optional[str] = None,
        ip: Optional[str] = None
    ) -> ProxyListResponse:
        """获取分页代理列表"""
        # 构建查询条件
        query = select(Proxy)
        count_query = select(func.count(Proxy.id))
        
        if status:
            query = query.filter(Proxy.status == status)
            count_query = count_query.filter(Proxy.status == status)
        if country:
            query = query.filter(Proxy.country == country)
            count_query = count_query.filter(Proxy.country == country)
        if ip:
            query = query.filter(Proxy.ip.ilike(f"%{ip}%"))
            count_query = count_query.filter(Proxy.ip.ilike(f"%{ip}%"))
            
        # 获取总数
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 获取分页数据
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(desc(Proxy.created_at))
        result = await self.db.execute(query)
        proxies = result.scalars().all()
        
        # 构建响应
        response = ProxyListResponse.create(proxies, total, page, size)
   
        return response

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
        min_success_rate: Optional[float] = None,
        min_quality_score: Optional[float] = None
    ) -> List[Proxy]:
        """获取可用代理"""
        query = select(Proxy).filter(Proxy.status == "ACTIVE")
        
        if country:
            query = query.filter(Proxy.country == country)
        if max_latency:
            query = query.filter(Proxy.latency <= max_latency)
        if min_success_rate:
            query = query.filter(Proxy.success_rate >= min_success_rate)
        
        # 先执行一个JOIN操作，确保只JOIN一次ProxyQuality表
        if min_quality_score is not None:
            # 使用辅助方法构建质量分数筛选条件
            quality_conditions = self._build_quality_score_filter(min_quality_score)
            
            # 使用LEFT JOIN以包含所有代理
            query = query.outerjoin(ProxyQuality)
            
            # 应用筛选条件
            if quality_conditions:
                query = query.filter(or_(*quality_conditions))
        else:
            # 如果不需要过滤质量分数，使用LEFT JOIN，这样可以包含没有质量记录的代理
            query = query.outerjoin(ProxyQuality)
            
        # 添加冷却时间检查
        quality_exists_query = select(ProxyQuality).where(ProxyQuality.proxy_id == Proxy.id).correlate(Proxy)
        quality_with_cooldown_query = select(ProxyQuality).where(
            and_(
                ProxyQuality.proxy_id == Proxy.id,
                or_(
                    ProxyQuality.last_used.is_(None),
                    # 使用简单的日期时间比较
                    func.extract('epoch', func.now() - ProxyQuality.last_used) >= ProxyQuality.cooldown_time
                )
            )
        ).correlate(Proxy)
        
        query = query.filter(
            or_(
                # 没有质量记录
                ~exists(quality_exists_query),
                # 或者已经超过冷却时间
                exists(quality_with_cooldown_query)
            )
        )
            
        # 排序：优先按质量评分降序，然后按延迟升序
        query = query.order_by(desc(ProxyQuality.quality_score), asc(Proxy.latency)).limit(limit)
        result = await self.db.execute(query)
        proxies = result.scalars().all()
        
        logger.debug(f"获取可用代理, count: {len(proxies)}, country: {country}, max_latency: {max_latency}, min_success_rate: {min_success_rate}, min_quality_score: {min_quality_score}")
        
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
        
    async def get_proxy_quality(self, proxy_id: str) -> Optional[ProxyQuality]:
        """获取代理质量记录"""
        result = await self.db.execute(
            select(ProxyQuality).filter(ProxyQuality.proxy_id == proxy_id)
        )
        quality = result.scalars().first()
        return quality
        
    async def create_proxy_quality(self, quality_data: ProxyQualityCreate) -> ProxyQuality:
        """创建代理质量记录"""
        quality = ProxyQuality(
            id=str(uuid.uuid4()),
            proxy_id=quality_data.proxy_id,
            total_usage=quality_data.total_usage,
            success_count=quality_data.success_count,
            quality_score=quality_data.quality_score,
            last_used=quality_data.last_used,
            cooldown_time=quality_data.cooldown_time
        )
        self.db.add(quality)
        await self.db.commit()
        await self.db.refresh(quality)
        
        logger.info(f"创建代理质量记录成功, proxy_id: {quality.proxy_id}, quality_score: {quality.quality_score}")
        return quality
        
    async def update_proxy_quality(self, proxy_id: str, quality_data: ProxyQualityUpdate) -> Optional[ProxyQuality]:
        """更新代理质量记录"""
        update_data = quality_data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.now()
        
        await self.db.execute(
            update(ProxyQuality)
            .where(ProxyQuality.proxy_id == proxy_id)
            .values(**update_data)
        )
        await self.db.commit()
        
        quality = await self.get_proxy_quality(proxy_id)
        if quality:
            logger.info(f"更新代理质量记录成功, proxy_id: {proxy_id}, fields: {list(update_data.keys())}")
        else:
            logger.error(f"更新代理质量记录失败，记录不存在, proxy_id: {proxy_id}")
        
        return quality
        
    async def record_proxy_usage(self, proxy_id: str, success: str) -> Tuple[Optional[Proxy], Optional[ProxyQuality]]:
        """记录代理使用情况并更新质量"""
        proxy = await self.get_proxy(proxy_id)
        if not proxy:
            logger.error(f"记录代理使用情况失败，代理不存在, proxy_id: {proxy_id}")
            return None, None
            
        quality = await self.get_proxy_quality(proxy_id)
        if not quality:
            # 创建默认质量记录
            quality = await self.create_proxy_quality(
                ProxyQualityCreate(
                    proxy_id=proxy_id,
                    total_usage=0,
                    success_count=0,
                    quality_score=0.8,
                    cooldown_time=0
                )
            )
        
        # 更新使用次数和成功次数
        total_usage = quality.total_usage + 1
        success_count = quality.success_count + (1 if success == "SUCCESS" else 0)
        
        # 计算新的质量得分
        # 基础成功率
        success_rate = success_count / total_usage if total_usage > 0 else 0
        
        # 考虑历史数据，权重调整
        if total_usage > 1:
            # 新的质量得分 = 历史质量 * 0.7 + 当前成功率 * 0.3
            quality_score = quality.quality_score * 0.7 + success_rate * 0.3
            
            # 如果当前请求失败，额外惩罚
            if success != "SUCCESS":
                quality_score *= 0.8
        else:
            quality_score = success_rate
            
        # 确保质量分数在0-1之间
        quality_score = max(0.0, min(1.0, quality_score))
        
        # 计算冷却时间（根据质量得分动态调整）
        # 质量越低，冷却时间越长
        if success == "SUCCESS":
            cooldown_time = int(30 * (1 - quality_score))  # 最长30秒冷却
        else:
            # 失败时，增加冷却时间
            cooldown_time = int(180 * (1 - quality_score))  # 最长180秒冷却
            
        # 更新质量记录
        quality = await self.update_proxy_quality(
            proxy_id,
            ProxyQualityUpdate(
                total_usage=total_usage,
                success_count=success_count,
                quality_score=quality_score,
                last_used=datetime.now(),
                cooldown_time=cooldown_time
            )
        )
        
        logger.info(f"记录代理使用情况, proxy_id: {proxy_id}, success: {success}, total_usage: {total_usage}, success_count: {success_count}, quality_score: {quality_score:.2f}, cooldown_time: {cooldown_time}")
        
        return proxy, quality
        
    async def get_rotating_proxy(
        self,
        country: Optional[str] = None,
        max_latency: Optional[int] = None,
        min_success_rate: Optional[float] = 0.5,
        min_quality_score: Optional[float] = 0.6
    ) -> Optional[Proxy]:
        """获取轮换代理（满足质量要求的可用代理）"""
        # 首先尝试获取满足质量要求的代理
        proxies = await self.get_available_proxies(
            limit=1,
            country=country,
            max_latency=max_latency,
            min_success_rate=min_success_rate,
            min_quality_score=min_quality_score
        )
        
        if proxies:
            logger.info(f"获取高质量轮换代理成功, proxy_id: {proxies[0].id}, ip: {proxies[0].ip}")
            return proxies[0]
            
        # 如果没有满足质量要求的代理，随机获取一个未达标的代理
        # 但排除掉那些质量分太低的代理
        logger.info(f"没有满足质量要求的代理，尝试随机获取")
        
        # 构建基础查询
        query = select(Proxy).filter(Proxy.status == "ACTIVE")
        
        # 先执行一个OUTERJOIN操作，确保只JOIN一次ProxyQuality表
        query = query.outerjoin(ProxyQuality)
        
        # 确保不使用质量特别差的代理
        query = query.filter(
            or_(
                # 没有质量记录
                ProxyQuality.id.is_(None),
                # 质量分不低于0.2
                ProxyQuality.quality_score >= 0.2
            )
        )
        
        if country:
            query = query.filter(Proxy.country == country)
            
        # 添加冷却时间检查
        query = query.filter(
            or_(
                # 没有质量记录
                ProxyQuality.id.is_(None),
                # 或者已经超过冷却时间
                and_(
                    or_(
                        ProxyQuality.last_used.is_(None),
                        # 使用简单的日期时间比较
                        func.extract('epoch', func.now() - ProxyQuality.last_used) >= ProxyQuality.cooldown_time
                    )
                )
            )
        )
            
        result = await self.db.execute(query)
        candidates = result.scalars().all()
        
        if not candidates:
            logger.warning(f"没有可用的代理")
            return None
            
        # 随机选择一个代理
        proxy = random.choice(candidates)
        logger.info(f"随机获取轮换代理成功, proxy_id: {proxy.id}, ip: {proxy.ip}")
        
        return proxy

    # 代理使用历史记录相关方法
    async def create_usage_history(self, history_data: ProxyUsageHistoryCreate) -> ProxyUsageHistory:
        """创建代理使用历史记录"""

        proxy = await self.get_proxy(history_data.proxy_id)
        if not proxy:
            raise ValueError(f"Proxy not found: {history_data.proxy_id}")
        
        # 获取代理质量信息
        quality = await self.get_proxy_quality(history_data.proxy_id)
        
        # 获取账户信息
        account_username_email = None
        if history_data.account_id:
            try:
                account_info = await self.account_client.get_account(history_data.account_id)
                if account_info :
                    account_username_email = account_info.get("username",  account_info.get("email", ""))
            except Exception as e:
                logger.warning(f"获取账户信息失败: {str(e)}")
        
        # 获取任务名称
        task_name = None
        if history_data.task_id:
            try:
                task_info = await self.scraper_client.get_task(history_data.task_id)
                if task_info:
                    task_name = task_info.get("task_name", "")
            except Exception as e:
                logger.warning(f"获取任务信息失败: {str(e)}")

        # 首先记录使用情况并更新质量
        proxy, quality = await self.record_proxy_usage(history_data.proxy_id, history_data.success)
        if not proxy:
            raise ValueError(f"Proxy not found: {history_data.proxy_id}")
        
        history = ProxyUsageHistory(
            id=str(uuid.uuid4()),
            proxy_id=history_data.proxy_id,
            account_id=history_data.account_id,
            task_id=history_data.task_id,
            service_name=history_data.service_name,
            success=history_data.success,
            response_time=history_data.response_time,
            proxy_ip=proxy.ip,
            proxy_port=proxy.port,
            account_username_email=account_username_email,
            task_name=task_name,
            quality_score=quality.quality_score if quality else 0.8,
            latency=proxy.latency
        )
        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(history)
        
        logger.info(f"创建代理使用历史记录成功, history_id: {history.id}, proxy_id: {history.proxy_id}, success: {history.success}")
        return history

    async def get_usage_history(self, history_id: str) -> Optional[ProxyUsageHistory]:
        """获取代理使用历史记录详情"""
        result = await self.db.execute(select(ProxyUsageHistory).filter(ProxyUsageHistory.id == history_id))
        history = result.scalars().first()
        
        if history:
            logger.debug(f"获取代理使用历史记录成功, history_id: {history_id}")
        else:
            logger.debug(f"代理使用历史记录不存在, history_id: {history_id}")
        
        return history

    async def get_usage_history_list(self, filter_data: ProxyUsageHistoryFilter) -> Tuple[List[ProxyUsageHistoryResponse], int]:
        """获取代理使用历史记录列表（优化版本，使用冗余字段减少关联查询）"""
        
        # 构建基础查询（现在只需要查询ProxyUsageHistory表）
        query = select(ProxyUsageHistory)
        
        # 应用过滤条件
        if filter_data.proxy_id:
            query = query.filter(ProxyUsageHistory.proxy_id == filter_data.proxy_id)
        
        if filter_data.proxy_ip:
            # 直接使用冗余字段进行筛选
            query = query.filter(ProxyUsageHistory.proxy_ip.ilike(f"%{filter_data.proxy_ip}%"))
        
        if filter_data.account_email:
            # 直接使用冗余字段进行筛选
            query = query.filter(ProxyUsageHistory.account_username_email.ilike(f"%{filter_data.account_email}%"))
        
        if filter_data.task_name:
            # 直接使用冗余字段进行筛选
            query = query.filter(ProxyUsageHistory.task_name.ilike(f"%{filter_data.task_name}%"))
        
        if filter_data.service_name:
            query = query.filter(ProxyUsageHistory.service_name == filter_data.service_name)
        
        if filter_data.success:
            query = query.filter(ProxyUsageHistory.success == filter_data.success)
        
        if filter_data.start_date:
            start_date = self._normalize_datetime(filter_data.start_date)
            query = query.filter(ProxyUsageHistory.created_at >= start_date)
        
        if filter_data.end_date:
            end_date = self._normalize_datetime(filter_data.end_date)
            query = query.filter(ProxyUsageHistory.created_at <= end_date)
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
         
        # 排序和分页
        query = query.order_by(desc(ProxyUsageHistory.created_at))
        query = query.offset((filter_data.page - 1) * filter_data.size).limit(filter_data.size)
        
        result = await self.db.execute(query)
        histories = result.scalars().all()
        
        # 直接构建响应，无需额外的关联查询
        history_list = []
        for history in histories:
            # 构建代理IP:端口格式
            proxy_ip_port = f"{history.proxy_ip}:{history.proxy_port}" if history.proxy_ip and history.proxy_port else ""
            
            history_item = ProxyUsageHistoryResponse(
                id=history.id,
                proxy_id=history.proxy_id,
                proxy_ip=proxy_ip_port,
                account_id=history.account_id,
                account_username_email=history.account_username_email,
                task_id=history.task_id,
                task_name=history.task_name,
                service_name=history.service_name,
                success=history.success,
                response_time=history.response_time,
                quality_score=history.quality_score,
                latency=history.latency,
                created_at=history.created_at,
                updated_at=history.updated_at,
                # 为了向后兼容，保留account_email字段
                account_email=history.account_username_email
            )
            
            history_list.append(history_item)
        
        logger.debug(f"获取代理使用历史记录列表成功（优化版本）, total: {total}, current_page_count: {len(history_list)}")
        return history_list, total

    async def get_proxy_usage_statistics(self, proxy_id: str, days: int = 7) -> Dict[str, Any]:
        """获取代理使用统计信息"""
        start_date = datetime.now() - timedelta(days=days)
        
        # 基础查询
        query = select(ProxyUsageHistory).filter(
            ProxyUsageHistory.proxy_id == proxy_id,
            ProxyUsageHistory.created_at >= start_date
        )
        
        result = await self.db.execute(query)
        histories = result.scalars().all()
        
        # 计算统计信息
        total_usage = len(histories)
        success_count = sum(1 for h in histories if h.success == "SUCCESS")
        failed_count = sum(1 for h in histories if h.success == "FAILED")
        timeout_count = sum(1 for h in histories if h.success == "TIMEOUT")
        
        success_rate = success_count / total_usage if total_usage > 0 else 0
        avg_response_time = sum(h.response_time or 0 for h in histories) / total_usage if total_usage > 0 else 0
        
        # 按日期分组统计
        daily_stats = {}
        for history in histories:
            date_key = history.created_at.strftime("%Y-%m-%d")
            if date_key not in daily_stats:
                daily_stats[date_key] = {"total": 0, "success": 0, "failed": 0, "timeout": 0}
            
            daily_stats[date_key]["total"] += 1
            if history.success == "SUCCESS":
                daily_stats[date_key]["success"] += 1
            elif history.success == "FAILED":
                daily_stats[date_key]["failed"] += 1
            elif history.success == "TIMEOUT":
                daily_stats[date_key]["timeout"] += 1
        
        statistics = {
            "proxy_id": proxy_id,
            "period_days": days,
            "total_usage": total_usage,
            "success_count": success_count,
            "failed_count": failed_count,
            "timeout_count": timeout_count,
            "success_rate": round(success_rate, 4),
            "avg_response_time": round(avg_response_time, 2),
            "daily_stats": daily_stats
        }
        
        logger.debug(f"获取代理使用统计信息成功, proxy_id: {proxy_id}, days: {days}")
        return statistics
    
    async def get_proxies_quality_info(
        self, 
        page: int = 1, 
        size: int = 20, 
        status: Optional[str] = None,
        country: Optional[str] = None,
        min_quality_score: Optional[float] = None,
        ip: Optional[str] = None
    ) -> tuple[List, int]:
        """获取代理质量信息列表（带分页）
        
        Args:
            page: 页码
            size: 每页数量
            status: 代理状态筛选
            country: 国家筛选
            min_quality_score: 最小质量分数筛选
            ip: IP地址筛选
        
        Returns:
            tuple: (代理质量信息列表, 总数量)
        """
        try:
            # 构建查询 - 联合查询代理和质量信息
            query = select(Proxy, ProxyQuality).outerjoin(
                ProxyQuality, Proxy.id == ProxyQuality.proxy_id
            )
            
            # 添加筛选条件
            if status:
                query = query.filter(Proxy.status == status)
            if country:
                query = query.filter(Proxy.country == country)
            if ip:
                query = query.filter(Proxy.ip.ilike(f"%{ip}%"))
            
            # 处理质量分数筛选
            if min_quality_score is not None:
                # 使用辅助方法构建质量分数筛选条件
                quality_conditions = self._build_quality_score_filter(min_quality_score)
                
                # 应用筛选条件
                if quality_conditions:
                    query = query.filter(or_(*quality_conditions))
            
            # 获取总数
            count_query = select(func.count()).select_from(
                query.subquery()
            )
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()
            
            # 分页
            offset = (page - 1) * size
            query = query.offset(offset).limit(size)
            
            # 执行查询
            result = await self.db.execute(query)
            rows = result.all()
            
            # 构造响应数据
            quality_info_list = []
            for proxy, quality in rows:       
                # 构造质量信息响应
                quality_info = {
                    "proxy_id": proxy.id,
                    "ip": proxy.ip,
                    "port": proxy.port,
                    "proxy_type": proxy.type,
                    "success_rate": proxy.success_rate,
                    "status": proxy.status,
                    "country": proxy.country,
                    "city": proxy.city,
                    "isp": proxy.isp,
                    "latency": proxy.latency,
                    "created_at": proxy.created_at,
                    "updated_at": proxy.updated_at
                }
                # 如果没有质量记录，创建默认值
                if quality is None:
                    quality_info["total_usage"] = 0
                    quality_info["success_count"] = 0
                    quality_info["quality_score"] = 0.8
                    quality_info["last_used"] = None
                else:
                    quality_info["total_usage"] = quality.total_usage
                    quality_info["success_count"] = quality.success_count
                    quality_info["quality_score"] = quality.quality_score
                    quality_info["last_used"] = quality.last_used
                
                quality_info_list.append(quality_info)
            
            return quality_info_list, total
            
        except Exception as e:
            logger.error(f"Error getting proxies quality info: {str(e)}")
            return [], 0