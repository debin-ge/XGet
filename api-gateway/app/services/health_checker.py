import asyncio
import logging
import time
from typing import Dict, Any
import httpx
from ..core.config import settings

logger = logging.getLogger(__name__)


class HealthChecker:
    """服务健康检查器"""
    
    def __init__(self):
        self.service_status = {}
        self.last_check_time = 0
        self.check_interval = settings.HEALTH_CHECK_INTERVAL_SECONDS
        self.check_timeout = settings.HEALTH_CHECK_TIMEOUT_SECONDS
        self.enabled = settings.HEALTH_CHECK_ENABLED
        self._check_task = None
        
    async def start(self):
        """启动健康检查"""
        if not self.enabled:
            logger.info("健康检查功能已禁用")
            return
            
        logger.info("启动服务健康检查")
        self._check_task = asyncio.create_task(self._periodic_check())
    
    async def stop(self):
        """停止健康检查"""
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
            logger.info("服务健康检查已停止")
    
    async def _periodic_check(self):
        """定期健康检查"""
        while True:
            try:
                await self.check_all_services()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查过程中发生错误: {str(e)}")
                await asyncio.sleep(5)  # 错误后短暂等待
    
    async def check_all_services(self):
        """检查所有服务的健康状态"""
        if not self.enabled:
            return
            
        current_time = time.time()
        self.last_check_time = current_time
        
        # 并发检查所有服务
        tasks = []
        for service_name, service_url in settings.SERVICES.items():
            task = asyncio.create_task(
                self._check_single_service(service_name, service_url)
            )
            tasks.append(task)
        
        # 等待所有检查完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理检查结果
        for i, result in enumerate(results):
            service_name = list(settings.SERVICES.keys())[i]
            if isinstance(result, Exception):
                logger.error(f"检查服务 {service_name} 时发生异常: {str(result)}")
                self.service_status[service_name] = {
                    "status": "error",
                    "last_check": current_time,
                    "error": str(result)
                }
            else:
                self.service_status[service_name] = result
        
        # 记录健康状态摘要
        healthy_count = sum(1 for status in self.service_status.values() if status["status"] == "healthy")
        total_count = len(self.service_status)
        logger.info(f"服务健康检查完成: {healthy_count}/{total_count} 服务健康")
    
    async def _check_single_service(self, service_name: str, service_url: str) -> Dict[str, Any]:
        """检查单个服务的健康状态"""
        start_time = time.time()
        
        # 使用更宽松的超时设置进行健康检查
        timeout_config = httpx.Timeout(
            connect=10.0,  # 连接超时
            read=15.0,     # 读取超时
            write=10.0,    # 写入超时
            pool=5.0       # 连接池超时
        )
        
        try:
            async with httpx.AsyncClient(
                timeout=timeout_config,
                http2=False,  # 禁用HTTP/2
                follow_redirects=True
            ) as client:
                response = await client.get(f"{service_url}/health")
                
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "response_time": elapsed,
                        "last_check": start_time,
                        "status_code": response.status_code
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "response_time": elapsed,
                        "last_check": start_time,
                        "status_code": response.status_code,
                        "error": f"HTTP {response.status_code}"
                    }
                    
        except httpx.TimeoutException:
            elapsed = time.time() - start_time
            return {
                "status": "timeout",
                "response_time": elapsed,
                "last_check": start_time,
                "error": "Request timeout"
            }
            
        except httpx.ConnectError:
            elapsed = time.time() - start_time
            return {
                "status": "unreachable",
                "response_time": elapsed,
                "last_check": start_time,
                "error": "Connection failed"
            }
            
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "status": "error",
                "response_time": elapsed,
                "last_check": start_time,
                "error": str(e)
            }
    
    def get_service_status(self, service_name: str = None) -> Dict[str, Any]:
        """获取服务状态"""
        if service_name:
            return self.service_status.get(service_name, {"status": "unknown"})
        return self.service_status.copy()
    
    def is_service_healthy(self, service_name: str) -> bool:
        """检查特定服务是否健康"""
        status = self.service_status.get(service_name, {})
        return status.get("status") == "healthy"
    
    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康状态摘要"""
        if not self.service_status:
            return {
                "overall_status": "unknown",
                "total_services": len(settings.SERVICES),
                "healthy_services": 0,
                "unhealthy_services": 0,
                "last_check": None
            }
        
        healthy_count = sum(1 for status in self.service_status.values() if status["status"] == "healthy")
        total_count = len(self.service_status)
        unhealthy_count = total_count - healthy_count
        
        # 确定整体状态
        if healthy_count == total_count:
            overall_status = "healthy"
        elif healthy_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return {
            "overall_status": overall_status,
            "total_services": total_count,
            "healthy_services": healthy_count,
            "unhealthy_services": unhealthy_count,
            "last_check": self.last_check_time,
            "services": self.service_status
        }


# 全局健康检查器实例
health_checker = HealthChecker() 