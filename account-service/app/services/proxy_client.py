import httpx
from typing import Dict, Optional
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)

class ProxyClient:
    """代理服务客户端，用于从代理服务获取代理信息"""
    
    def __init__(self):
        self.base_url = settings.PROXY_SERVICE_URL
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def get_proxy(self, proxy_id: str) -> Optional[Dict]:
        """获取指定ID的代理信息"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/proxies/{proxy_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"获取代理信息失败: {e}")
            return None
    
    async def get_available_proxy(self) -> Optional[Dict]:
        """获取一个可用的代理"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/proxies/available")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"获取可用代理失败: {e}")
            return None 