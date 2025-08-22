import httpx
from typing import Dict, Optional
from ..core.config import settings
from ..core.logging import logger


class ProxyClient:
    """代理服务客户端，用于从代理服务获取代理信息并记录使用情况"""
    
    def __init__(self):
        self.base_url = settings.PROXY_SERVICE_URL
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def get_proxy(self, proxy_id: str) -> Optional[Dict]:
        """获取指定ID的代理信息"""
        try:
            response = await self.client.get(f"{self.base_url}{settings.API_V1_STR}/proxies/{proxy_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"获取代理信息失败: {e}")
            return None
    
    async def get_available_proxy(
        self, 
        country: Optional[str] = None,
        max_latency: Optional[int] = None,
        min_success_rate: Optional[float] = None,
        min_quality_score: Optional[float] = None
    ) -> Optional[Dict]:
        """获取一个可用的代理"""
        try:
            params = {}
            if country:
                params["country"] = country
            if max_latency:
                params["max_latency"] = max_latency
            if min_success_rate:
                params["min_success_rate"] = min_success_rate
            if min_quality_score:
                params["min_quality_score"] = min_quality_score
                
            response = await self.client.get(f"{self.base_url}/api/v1/proxies/available", params=params)
            response.raise_for_status()
            proxies = response.json()
            if proxies and len(proxies) > 0:
                return proxies[0]
            return None
        except httpx.HTTPError as e:
            logger.error(f"获取可用代理失败: {e}")
            return None

    async def get_rotating_proxy(
        self,
        country: Optional[str] = None,
        min_quality_score: Optional[float] = 0.6
    ) -> Optional[Dict]:
        """获取一个轮换代理（高质量）"""
        try:
            params = {}
            if country:
                params["country"] = country
            if min_quality_score:
                params["min_quality_score"] = min_quality_score
                
            response = await self.client.post(f"{self.base_url}/api/v1/proxies/rotate", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"获取轮换代理失败: {e}")
            return None
            
    async def record_proxy_usage(
        self, 
        proxy_id: str, 
        success: str,
        task_id: Optional[str] = None,
        account_id: Optional[str] = None,
        service_name: Optional[str] = None,
        response_time: Optional[int] = None,
        proxy_ip: Optional[str] = None,
        proxy_port: Optional[int] = None,
        account_username_email: Optional[str] = None,
        task_name: Optional[str] = None,
        quality_score: Optional[float] = None,
        latency: Optional[int] = None
    ) -> bool:
        """记录代理使用结果"""
        if not proxy_id:
            logger.warning("无法记录代理使用结果：代理ID为空")
            return False
            
        try:
            # 构建请求数据，匹配新的ProxyUsageHistoryCreate schema
            data = {
                "proxy_id": proxy_id,
                "task_id": task_id,
                "account_id": account_id,
                "service_name": service_name or "scraper-service",
                "success": success,
                "response_time": response_time,
                "proxy_ip": proxy_ip,
                "proxy_port": proxy_port,
                "account_username_email": account_username_email,
                "task_name": task_name,
                "quality_score": quality_score,
                "latency": latency
            }
            
            # 移除None值
            data = {k: v for k, v in data.items() if v is not None}
            
            # 使用新的API端点
            response = await self.client.post(f"{self.base_url}/api/v1/proxies/usage/history", json=data)
            response.raise_for_status()
            
            logger.info(f"记录代理使用结果成功: proxy_id={proxy_id}, success={success}, service={data.get('service_name')}")
            return True
        except httpx.HTTPError as e:
            logger.error(f"记录代理使用结果失败: proxy_id={proxy_id}, success={success}, error={e}")
            return False 