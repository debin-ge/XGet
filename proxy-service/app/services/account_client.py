import httpx
from typing import Dict, Optional
from ..core.config import settings
from ..core.logging import logger

class AccountClient:
    """账号服务客户端，用于从账号服务获取账号信息"""
    
    def __init__(self):
        self.base_url = settings.ACCOUNT_SERVICE_URL
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def get_account(self, account_id: str) -> Optional[Dict]:
        """获取指定ID的账号信息"""
        try:
            response = await self.client.get(f"{self.base_url}{settings.API_V1_STR}/accounts/{account_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"获取账号信息失败: {e}")
            return None