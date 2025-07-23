from fastapi import Request, HTTPException, status
import httpx
import logging
from typing import Dict, Any, Optional
from ..core.config import settings
import time
import json

logger = logging.getLogger(__name__)


class ServiceRouter:
    """服务路由器，负责将请求转发到对应的微服务"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.services = settings.SERVICES
    
    async def forward_request(
        self, 
        request: Request, 
        service_name: str, 
        path: str,
        include_token: bool = True
    ) -> Dict[str, Any]:
        """
        将请求转发到指定的服务
        
        Args:
            request: 原始请求
            service_name: 服务名称
            path: 请求路径
            include_token: 是否包含认证令牌
            
        Returns:
            响应数据
        """
        if service_name not in self.services:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service '{service_name}' not found"
            )
        
        service_url = self.services[service_name]
        target_url = f"{service_url}{path}"
        
        # 获取请求方法
        method = request.method
        
        # 获取请求头
        headers = dict(request.headers)
        headers.pop("host", None)
        
        # 如果不需要包含认证令牌，则移除Authorization头
        if not include_token:
            headers.pop("authorization", None)
        
        # 获取查询参数
        params = dict(request.query_params)
        
        # 获取请求体
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            body_bytes = await request.body()
            if body_bytes:
                try:
                    content_type = request.headers.get("content-type", "")
                    if "application/json" in content_type:
                        body = json.loads(body_bytes)
                    else:
                        body = body_bytes
                except Exception as e:
                    logger.error(f"Failed to parse request body: {e}")
                    body = body_bytes
        
        start_time = time.time()
        try:
            # 发送请求到目标服务
            response = await self.client.request(
                method=method,
                url=target_url,
                headers=headers,
                params=params,
                json=body if isinstance(body, dict) else None,
                content=body if not isinstance(body, dict) and body is not None else None,
            )
            
            # 记录请求时间和状态码
            elapsed = time.time() - start_time
            logger.info(
                f"Request to {service_name} completed in {elapsed:.3f}s with status {response.status_code}"
            )
            
            # 解析响应
            try:
                response_data = response.json()
            except Exception:
                response_data = {"content": response.text}
            
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "data": response_data
            }
        except httpx.RequestError as e:
            elapsed = time.time() - start_time
            logger.error(f"Request to {service_name} failed after {elapsed:.3f}s: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service '{service_name}' is unavailable: {str(e)}"
            )

service_router = ServiceRouter() 