from pydantic_settings import BaseSettings
from typing import Dict, List, Optional
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "XGet API Gateway"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS设置
    CORS_ORIGINS: List[str] = ["*"]
    
    # 服务发现配置
    SERVICE_DISCOVERY_TYPE: str = os.getenv("SERVICE_DISCOVERY_TYPE", "static")  # static, consul, kubernetes
    
    # 静态服务列表 - 修正服务名称映射
    SERVICES: Dict[str, str] = {
        "account-service": os.getenv("ACCOUNT_SERVICE_URL", "http://account-service:8000"),
        "proxy-service": os.getenv("PROXY_SERVICE_URL", "http://proxy-service:8000"),
        "scraper-service": os.getenv("SCRAPER_SERVICE_URL", "http://scraper-service:8000"),
        "user-service": os.getenv("USER_SERVICE_URL", "http://user-service:8000"),
    }
    
    # 服务健康检查配置
    HEALTH_CHECK_ENABLED: bool = os.getenv("HEALTH_CHECK_ENABLED", "True").lower() == "true"
    HEALTH_CHECK_INTERVAL_SECONDS: int = int(os.getenv("HEALTH_CHECK_INTERVAL_SECONDS", "30"))
    HEALTH_CHECK_TIMEOUT_SECONDS: int = int(os.getenv("HEALTH_CHECK_TIMEOUT_SECONDS", "5"))
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOG_DIR: Optional[str] = os.getenv("LOG_DIR")
    
    # 限流配置
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_PERIOD_SECONDS: int = int(os.getenv("RATE_LIMIT_PERIOD_SECONDS", "60"))
    RATE_LIMIT_BURST: int = int(os.getenv("RATE_LIMIT_BURST", "10"))
    
    # Redis配置（用于限流和缓存）
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_URL: str = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
    
    # JWT认证配置
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # 代理和转发配置 - 针对网络不稳定优化的默认值
    PROXY_TIMEOUT_SECONDS: float = float(os.getenv("PROXY_TIMEOUT_SECONDS", "45.0"))  # 增加读取超时
    PROXY_CONNECT_TIMEOUT_SECONDS: float = float(os.getenv("PROXY_CONNECT_TIMEOUT_SECONDS", "15.0"))  # 增加连接超时
    PROXY_WRITE_TIMEOUT_SECONDS: float = float(os.getenv("PROXY_WRITE_TIMEOUT_SECONDS", "15.0"))  # 增加写入超时
    PROXY_POOL_TIMEOUT_SECONDS: float = float(os.getenv("PROXY_POOL_TIMEOUT_SECONDS", "10.0"))  # 增加连接池超时
    PROXY_RETRIES: int = int(os.getenv("PROXY_RETRIES", "5"))  # 增加重试次数
    PROXY_RETRY_DELAY_SECONDS: float = float(os.getenv("PROXY_RETRY_DELAY_SECONDS", "2.0"))  # 增加重试延迟
    PROXY_MAX_KEEPALIVE_CONNECTIONS: int = int(os.getenv("PROXY_MAX_KEEPALIVE_CONNECTIONS", "15"))  # 减少保活连接
    PROXY_MAX_CONNECTIONS: int = int(os.getenv("PROXY_MAX_CONNECTIONS", "75"))  # 减少最大连接数
    PROXY_KEEPALIVE_EXPIRY: float = float(os.getenv("PROXY_KEEPALIVE_EXPIRY", "60.0"))  # 增加连接保活时间
    
    # 监控和指标配置
    METRICS_ENABLED: bool = os.getenv("METRICS_ENABLED", "True").lower() == "true"
    METRICS_PATH: str = os.getenv("METRICS_PATH", "/metrics")
    
    # 安全配置
    SECURITY_HEADERS_ENABLED: bool = os.getenv("SECURITY_HEADERS_ENABLED", "True").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings() 