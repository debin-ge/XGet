import json
import time
import asyncio
from typing import Dict, Any, Optional, Union
from fastapi import Request, HTTPException, status
from loguru import logger
import httpx
from app.core.config import settings
from .monitoring import metrics_collector


class ServiceRouter:
    """服务路由器，负责将请求转发到相应的微服务"""

    def __init__(self):
        # 服务配置映射
        self.services = {
            "user-service": settings.SERVICES["user-service"],
            "account-service": settings.SERVICES["account-service"],
            "proxy-service": settings.SERVICES["proxy-service"],
            "scraper-service": settings.SERVICES["scraper-service"],
        }
        
        # 创建HTTP客户端
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=settings.PROXY_CONNECT_TIMEOUT_SECONDS,
                read=settings.PROXY_TIMEOUT_SECONDS,
                write=settings.PROXY_WRITE_TIMEOUT_SECONDS,
                pool=settings.PROXY_POOL_TIMEOUT_SECONDS
            ),
            limits=httpx.Limits(
                max_keepalive_connections=settings.PROXY_MAX_KEEPALIVE_CONNECTIONS,
                max_connections=settings.PROXY_MAX_CONNECTIONS,
                keepalive_expiry=settings.PROXY_KEEPALIVE_EXPIRY
            ),
            follow_redirects=True
        )
        
        # 创建备用客户端，用于处理Content-Length相关问题
        self.fallback_client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=settings.PROXY_CONNECT_TIMEOUT_SECONDS,
                read=settings.PROXY_TIMEOUT_SECONDS * 2,  # 更长的读取超时
                write=settings.PROXY_WRITE_TIMEOUT_SECONDS,
                pool=settings.PROXY_POOL_TIMEOUT_SECONDS
            ),
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=5.0  # 更短的keepalive
            ),
            http2=False,  # 禁用HTTP/2
            follow_redirects=True
        )
        
        logger.info(f"ServiceRouter initialized with services: {list(self.services.keys())}")

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()
        await self.fallback_client.aclose()
        logger.info("ServiceRouter clients closed")

    def _prepare_headers(self, request: Request, include_token: bool = True) -> Dict[str, str]:
        """准备请求头部，移除可能导致冲突的头部，并添加用户信息"""
        headers = dict(request.headers)
        headers.pop("host", None)
        
        # 如果不需要包含认证令牌，则移除Authorization头
        if not include_token:
            headers.pop("authorization", None)
        
        # 移除可能导致冲突的头部，这些头部会由httpx自动管理
        headers.pop("content-length", None)
        headers.pop("transfer-encoding", None)
        
        # 添加用户信息到请求头（如果存在）
        if hasattr(request.state, "user") and request.state.user:
            user_info = request.state.user
            # 添加用户ID到请求头
            if "id" in user_info:
                headers["X-User-ID"] = str(user_info["id"])
            # 添加用户名到请求头
            if "username" in user_info:
                headers["X-Username"] = str(user_info["username"])
            # 添加用户角色到请求头
            if "roles" in user_info:
                headers["X-User-Roles"] = ",".join(user_info["roles"])
            # 添加是否为超级用户标识
            if "is_superuser" in user_info:
                headers["X-Is-Superuser"] = str(user_info["is_superuser"]).lower()
        
        return headers

    async def _prepare_body(self, request: Request) -> Optional[Union[Dict, bytes]]:
        """准备请求体，根据Content-Type进行适当的解析"""
        method = request.method
        if method not in ["POST", "PUT", "PATCH"]:
            return None

        body_bytes = await request.body()
        if not body_bytes:
            logger.debug(f"No body content for {method} request")
            return None

        try:
            content_type = request.headers.get("content-type", "")
            logger.debug(f"Processing body: content-type={content_type}, length={len(body_bytes)}")
            
            if "application/json" in content_type:
                body = json.loads(body_bytes)
                logger.debug(f"Parsed JSON body with {len(body)} fields")
                return body
            else:
                logger.debug(f"Using raw body, length: {len(body_bytes)}")
                return body_bytes
                
        except Exception as e:
            logger.error(f"Failed to parse request body: {e}")
            return body_bytes

    def _prepare_request_kwargs(self, method: str, url: str, headers: Dict[str, str], 
                               params: Dict[str, str], body: Any) -> Dict[str, Any]:
        """准备httpx请求参数"""
        request_kwargs = {
            "method": method,
            "url": url,
            "headers": headers,
            "params": params,
        }
        
        if body is not None:
            if isinstance(body, dict):
                # JSON数据：序列化为字符串并作为content发送
                json_str = json.dumps(body)
                request_kwargs["content"] = json_str.encode('utf-8')
                # 确保Content-Type正确设置
                if "content-type" not in {k.lower() for k in headers.keys()}:
                    headers["Content-Type"] = "application/json"
                logger.debug(f"Prepared JSON content: {len(json_str)} bytes")
                
            elif isinstance(body, (str, bytes)):
                request_kwargs["content"] = body
                logger.debug(f"Prepared raw content: {len(body)} bytes")
                
            else:
                # 其他类型：尝试序列化为JSON
                try:
                    json_str = json.dumps(body)
                    request_kwargs["content"] = json_str.encode('utf-8')
                    if "content-type" not in {k.lower() for k in headers.keys()}:
                        headers["Content-Type"] = "application/json"
                    logger.debug(f"Prepared serialized content: {len(json_str)} bytes")
                except:
                    request_kwargs["content"] = str(body).encode('utf-8')
                    logger.debug(f"Prepared stringified content: {len(str(body))} bytes")
        
        return request_kwargs

    async def forward_request(
        self,
        request: Request,
        service_name: str,
        path: str,
        include_token: bool = True
    ) -> Dict[str, Any]:
        """将请求转发到指定的微服务"""
        
        # 验证服务是否存在
        if service_name not in self.services:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service '{service_name}' not found"
            )
        
        service_url = self.services[service_name]
        target_url = f"{service_url}{path}"

        logger.info(f"Forwarding {request.method} request to {service_name} at {target_url}")
        
        # 准备请求组件
        headers = self._prepare_headers(request, include_token)
        params = dict(request.query_params)
        body = await self._prepare_body(request)
        
        # 执行请求，带重试机制
        return await self._execute_request_with_retry(
            method=request.method,
            url=target_url,
            headers=headers,
            params=params,
            body=body,
            service_name=service_name,
            use_fallback=False  # 初始使用主客户端
        )
    
    async def _execute_request_with_retry(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Dict[str, str],
        body: Any,
        service_name: str,
        use_fallback: bool = False
    ) -> Dict[str, Any]:
        """执行带重试机制的请求"""
        last_exception = None
        
        for attempt in range(settings.PROXY_RETRIES + 1):
            start_time = time.time()
            
            # 选择客户端
            client = self.fallback_client if use_fallback else self.client
            client_type = "fallback" if use_fallback else "main"
            
            # 日志记录
            if attempt == 0:
                logger.debug(f"Sending {method} request to {service_name} using {client_type} client")
            else:
                logger.debug(f"Retry {attempt} for {method} request to {service_name} using {client_type} client")
            
            try:
                # 准备请求参数
                request_kwargs = self._prepare_request_kwargs(method, url, headers, params, body)
                
                # 发送请求
                response = await client.request(**request_kwargs)
                
                # 确保响应内容被完全读取
                try:
                    await response.aread()
                except Exception as read_error:
                    logger.warning(f"Response read issue for {service_name}: {read_error}")
                
                # 记录成功的请求
                elapsed = time.time() - start_time
                logger.info(f"Request to {service_name} completed in {elapsed:.3f}s with status {response.status_code} (attempt {attempt + 1})")
                
                # 记录监控指标
                metrics_collector.record_service_request(
                    service=service_name,
                    status_code=response.status_code,
                    duration=elapsed
                )
                
                # 解析响应
                response_data = self._parse_response(response, service_name)
                
                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "data": response_data
                }
                
            except (httpx.RequestError, httpx.LocalProtocolError) as e:
                elapsed = time.time() - start_time
                last_exception = e
                
                # 记录监控指标
                metrics_collector.record_service_request(
                    service=service_name,
                    status_code=503,
                    duration=elapsed
                )
                
                # 处理重试逻辑
                if not await self._handle_retry_logic(e, attempt, service_name, method, url, headers, params, body, use_fallback):
                    break
            
            except Exception as e:
                elapsed = time.time() - start_time
                last_exception = e
                
                # 记录监控指标
                metrics_collector.record_service_request(
                    service=service_name,
                    status_code=500,
                    duration=elapsed
                )
                
                logger.error(f"Unexpected error when requesting {service_name}: {str(e)}")
                break
        
        # 所有重试都失败了
        error_detail = f"Service '{service_name}' is unavailable after {settings.PROXY_RETRIES + 1} attempts"
        if last_exception:
            error_detail += f": {type(last_exception).__name__}: {str(last_exception)}"
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_detail
        )

    def _parse_response(self, response: httpx.Response, service_name: str) -> Any:
        """解析HTTP响应"""
        try:
            # 检查Content-Length是否匹配
            content_length = response.headers.get('content-length')
            if content_length:
                expected_length = int(content_length)
                actual_length = len(response.content)
                if actual_length != expected_length:
                    logger.warning(
                        f"Content-Length mismatch for {service_name}: expected {expected_length}, got {actual_length}"
                    )
            
            # 解析JSON响应
            return response.json()
            
        except ValueError as e:
            logger.warning(f"Failed to parse JSON from {service_name}: {e}")
            return {"content": response.text}
            
        except Exception as e:
            logger.error(f"Error processing response from {service_name}: {e}")
            return {"content": response.text}

    async def _handle_retry_logic(self, error: Exception, attempt: int, service_name: str,
                                  method: str, url: str, headers: Dict[str, str], 
                                  params: Dict[str, str], body: Any, use_fallback: bool) -> bool:
        """处理重试逻辑，返回是否继续重试"""
        error_str = str(error).lower()
        is_content_length_error = "too little data for declared content-length" in error_str
        
        if is_content_length_error:
            logger.warning(f"Content-Length protocol error for {service_name} (attempt {attempt + 1}): {str(error)}")
        
        # 检查是否可重试
        is_retryable = self._is_retryable_error(error)
        
        if attempt < settings.PROXY_RETRIES and is_retryable:
            # 如果是Content-Length错误且还没使用备用客户端，切换到备用客户端
            if is_content_length_error and not use_fallback:
                logger.info(f"Switching to fallback client for {service_name} due to Content-Length error")
                await self._execute_request_with_retry(
                    method=method, url=url, headers=headers, params=params, 
                    body=body, service_name=service_name, use_fallback=True
                )
                return False  # 已处理，不需要继续当前重试循环
            
            # 计算重试延迟
            if is_content_length_error:
                retry_delay = min(settings.PROXY_RETRY_DELAY_SECONDS * (1.5 ** attempt), 5.0)
            else:
                retry_delay = settings.PROXY_RETRY_DELAY_SECONDS * (2 ** attempt)
            
            logger.warning(
                f"Request to {service_name} failed (attempt {attempt + 1}): {type(error).__name__}: {str(error)}. "
                f"Retrying in {retry_delay:.1f}s..."
            )
            await asyncio.sleep(retry_delay)
            return True  # 继续重试
        else:
            logger.error(f"Request to {service_name} failed after {attempt + 1} attempts: {type(error).__name__}: {str(error)}")
            return False  # 停止重试

    def _is_retryable_error(self, error: Exception) -> bool:
        """判断错误是否可以重试"""
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # 网络相关的可重试错误模式
        retryable_patterns = [
            "connection", "timeout", "too little data for declared content-length",
            "connection reset", "connection aborted", "read timeout", "pool timeout",
            "server disconnected", "incomplete read"
        ]
        
        # 特定的httpx错误类型
        retryable_types = [
            "ConnectTimeout", "ReadTimeout", "PoolTimeout", "NetworkError",
            "RemoteProtocolError", "LocalProtocolError"
        ]
        
        # 检查错误消息
        if any(pattern in error_str for pattern in retryable_patterns):
            return True
        
        # 检查错误类型
        if error_type in retryable_types:
            return True
            
        # HTTPStatusError - 某些HTTP状态码可以重试
        if hasattr(error, 'response'):
            status_code = getattr(error.response, 'status_code', None)
            if status_code in [502, 503, 504, 429]:
                return True
        
        return False


# 全局服务路由器实例
service_router = ServiceRouter() 