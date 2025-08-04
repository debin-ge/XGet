from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, desc, asc, or_, and_, func, exists, String, Integer
from ..models.proxy import Proxy, ProxyQuality
from ..schemas.proxy import ProxyCreate, ProxyUpdate, ProxyCheckResult, ProxyQualityCreate, ProxyQualityUpdate
from ..core.logging import logger
import uuid
from datetime import datetime, timedelta
import aiohttp
import asyncio
import random


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
            query = query.join(ProxyQuality).filter(ProxyQuality.quality_score >= min_quality_score)
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
        
    async def record_proxy_usage(self, proxy_id: str, success: bool) -> Tuple[Optional[Proxy], Optional[ProxyQuality]]:
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
        success_count = quality.success_count + (1 if success else 0)
        
        # 计算新的质量得分
        # 基础成功率
        success_rate = success_count / total_usage if total_usage > 0 else 0
        
        # 考虑历史数据，权重调整
        if total_usage > 1:
            # 新的质量得分 = 历史质量 * 0.7 + 当前成功率 * 0.3
            quality_score = quality.quality_score * 0.7 + success_rate * 0.3
            
            # 如果当前请求失败，额外惩罚
            if not success:
                quality_score *= 0.8
        else:
            quality_score = success_rate
            
        # 确保质量分数在0-1之间
        quality_score = max(0.0, min(1.0, quality_score))
        
        # 计算冷却时间（根据质量得分动态调整）
        # 质量越低，冷却时间越长
        if success:
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
            proxy = proxies[0]
            logger.info(f"获取高质量轮换代理成功, proxy_id: {proxy.id}, ip: {proxy.ip}")
            return proxy
            
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