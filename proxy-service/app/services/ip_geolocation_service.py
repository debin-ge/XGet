import aiohttp
import asyncio
from typing import Dict, Optional, Tuple
from ..core.logging import logger
from ..core.config import settings


class IPGeolocationService:
    """IP地理位置查询服务
    
    支持多个免费API提供商：
    1. ip-api.com (免费，1000次/分钟)
    2. ipapi.co (免费，1000次/天)
    3. geojs.io (免费，无限制)
    """
    
    def __init__(self):
        self.timeout = getattr(settings, 'IP_GEOLOCATION_TIMEOUT', 10)
        self.retry_attempts = getattr(settings, 'IP_GEOLOCATION_RETRY_ATTEMPTS', 3)
        
        # API提供商列表（按优先级排序）
        self.providers = [
            {
                'name': 'ip-api',
                'url': 'http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query',
                'parse_method': self._parse_ip_api
            },
            {
                'name': 'ipapi',
                'url': 'https://ipapi.co/{ip}/json/',
                'parse_method': self._parse_ipapi
            },
            {
                'name': 'geojs',
                'url': 'https://get.geojs.io/v1/ip/geo/{ip}.json',
                'parse_method': self._parse_geojs
            }
        ]
    
    async def get_ip_info(self, ip: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        获取IP地址的地理位置信息
        
        Args:
            ip: IP地址
            
        Returns:
            Tuple[country, city, isp]: 国家、城市、ISP信息
        """
        if not ip or not self._is_valid_ip(ip):
            logger.warning(f"无效的IP地址: {ip}")
            return None, None, None
        
        # 尝试每个API提供商
        for provider in self.providers:
            try:
                country, city, isp = await self._query_provider(provider, ip)
                if country:  # 如果成功获取到国家信息，认为查询成功
                    logger.info(f"IP地理位置查询成功 - Provider: {provider['name']}, IP: {ip}, Country: {country}, City: {city}, ISP: {isp}")
                    return country, city, isp
            except Exception as e:
                logger.warning(f"IP地理位置查询失败 - Provider: {provider['name']}, IP: {ip}, Error: {str(e)}")
                continue
        
        logger.error(f"所有IP地理位置查询提供商都失败 - IP: {ip}")
        return None, None, None
    
    async def _query_provider(self, provider: Dict, ip: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """查询单个API提供商"""
        url = provider['url'].format(ip=ip)
        
        for attempt in range(self.retry_attempts):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            return provider['parse_method'](data)
                        else:
                            logger.warning(f"API返回错误状态码: {response.status} - Provider: {provider['name']}, IP: {ip}")
            except asyncio.TimeoutError:
                logger.warning(f"API请求超时 - Provider: {provider['name']}, IP: {ip}, Attempt: {attempt + 1}")
            except Exception as e:
                logger.warning(f"API请求异常 - Provider: {provider['name']}, IP: {ip}, Attempt: {attempt + 1}, Error: {str(e)}")
            
            if attempt < self.retry_attempts - 1:
                await asyncio.sleep(1)  # 重试前等待1秒
        
        raise Exception(f"所有重试都失败 - Provider: {provider['name']}")
    
    def _parse_ip_api(self, data: Dict) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """解析ip-api.com的响应"""
        if data.get('status') != 'success':
            raise Exception(f"API返回错误: {data.get('message', 'Unknown error')}")
        
        country = data.get('country')
        city = data.get('city')
        isp = data.get('isp') or data.get('org')
        
        return country, city, isp
    
    def _parse_ipapi(self, data: Dict) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """解析ipapi.co的响应"""
        if 'error' in data:
            raise Exception(f"API返回错误: {data.get('reason', 'Unknown error')}")
        
        country = data.get('country_name')
        city = data.get('city')
        isp = data.get('org')
        
        return country, city, isp
    
    def _parse_geojs(self, data: Dict) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """解析geojs.io的响应"""
        country = data.get('country')
        city = data.get('city')
        isp = data.get('organization_name')
        
        return country, city, isp
    
    def _is_valid_ip(self, ip: str) -> bool:
        """简单的IP地址格式验证"""
        if not ip:
            return False
        
        # 检查是否为私有IP或本地IP
        if ip.startswith(('127.', '10.', '172.', '192.168.', 'localhost', '::1')):
            return False
        
        # 简单的IPv4格式检查
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        try:
            for part in parts:
                num = int(part)
                if not 0 <= num <= 255:
                    return False
            return True
        except ValueError:
            return False


# 全局实例
ip_geolocation_service = IPGeolocationService() 