import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..db.database import SessionLocal
from .proxy_service import ProxyService

logger = logging.getLogger(__name__)

class ProxyScheduler:
    def __init__(self):
        self.running = False
        self.check_interval = 300  # 5分钟检查一次

    async def start(self):
        """启动定时任务"""
        self.running = True
        while self.running:
            try:
                await self.check_proxies()
            except Exception as e:
                logger.error(f"代理检查任务异常: {e}")
            
            await asyncio.sleep(self.check_interval)

    async def stop(self):
        """停止定时任务"""
        self.running = False

    async def check_proxies(self):
        """检查代理可用性"""
        logger.info("开始检查代理可用性")
        
        async with SessionLocal() as db:
            service = ProxyService(db)
            
            # 获取需要检查的代理
            proxies = await service.get_proxies_for_check(limit=50)
            
            if not proxies:
                logger.info("没有需要检查的代理")
                return
            
            logger.info(f"找到 {len(proxies)} 个需要检查的代理")
            
            # 检查代理
            for proxy in proxies:
                try:
                    logger.info(f"检查代理: {proxy.type}://{proxy.ip}:{proxy.port}")
                    await service.check_proxy(proxy)
                except Exception as e:
                    logger.error(f"检查代理异常: {proxy.id} - {e}")
            
            logger.info("代理检查完成")

proxy_scheduler = ProxyScheduler()
