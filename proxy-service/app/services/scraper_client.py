import httpx
from typing import Dict, Optional
from ..core.config import settings
from ..core.logging import logger

class ScraperClient:
    """任务服务客户端，用于从任务服务获取任务信息"""
    
    def __init__(self):
        self.base_url = settings.SCRAPER_SERVICE_URL
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def get_task(self, task_id: str) -> Optional[Dict]:
        """获取指定ID的任务信息"""
        try:
            response = await self.client.get(f"{self.base_url}{settings.API_V1_STR}/tasks/{task_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"获取任务信息失败: {e}")
            return None