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
    
    # 静态服务列表
    SERVICES: Dict[str, str] = {
        "account": os.getenv("ACCOUNT_SERVICE_URL", "http://account-service:8000"),
        "proxy": os.getenv("PROXY_SERVICE_URL", "http://proxy-service:8000"),
        "scraper": os.getenv("SCRAPER_SERVICE_URL", "http://scraper-service:8000"),
        "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000"),
        "user": os.getenv("USER_SERVICE_URL", "http://user-service:8000"),
        "storage": os.getenv("STORAGE_SERVICE_URL", "http://storage-service:8000"),
        "processing": os.getenv("PROCESSING_SERVICE_URL", "http://processing-service:8000"),
        "analytics": os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8000"),
        "monitoring": os.getenv("MONITORING_SERVICE_URL", "http://monitoring-service:8000"),
    }
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # 限流配置
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_PERIOD_SECONDS: int = int(os.getenv("RATE_LIMIT_PERIOD_SECONDS", "60"))
    
    # Redis配置（用于限流和缓存）
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # JWT认证配置
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings() 