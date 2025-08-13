from fastapi import Request
from fastapi.responses import Response
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)


async def security_headers_middleware(request: Request, call_next):
    """安全头中间件"""
    response = await call_next(request)
    
    if not settings.SECURITY_HEADERS_ENABLED:
        return response
    
    # 添加安全头
    security_headers = {
        # 防止XSS攻击
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        
        # HTTPS相关
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        
        # 内容安全策略
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        ),
        
        # 引用策略
        "Referrer-Policy": "strict-origin-when-cross-origin",
        
        # 权限策略
        "Permissions-Policy": (
            "geolocation=(), "
            "camera=(), "
            "microphone=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        ),
        
        # 服务器信息隐藏
        "Server": "XGet-Gateway"
    }
    
    # 应用安全头
    for header, value in security_headers.items():
        response.headers[header] = value
    
    # 移除可能泄露信息的头
    headers_to_remove = ["server", "x-powered-by"]
    for header in headers_to_remove:
        if header in response.headers:
            del response.headers[header]
    
    return response


def validate_request_size(max_size: int = 10 * 1024 * 1024):  # 10MB default
    """请求大小验证装饰器"""
    async def middleware(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                content_length = int(content_length)
                if content_length > max_size:
                    return Response(
                        content="Request entity too large",
                        status_code=413,
                        headers={"Content-Type": "text/plain"}
                    )
            except ValueError:
                pass
        
        return await call_next(request)
    
    return middleware


async def request_id_middleware(request: Request, call_next):
    """请求ID中间件"""
    import uuid
    
    # 生成唯一请求ID
    request_id = str(uuid.uuid4())
    
    # 添加到请求状态
    request.state.request_id = request_id
    
    # 处理请求
    response = await call_next(request)
    
    # 添加请求ID到响应头
    response.headers["X-Request-ID"] = request_id
    
    return response 