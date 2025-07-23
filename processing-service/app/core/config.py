import os
from typing import Any, Dict, List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "XGet Processing Service"
    
    # PostgreSQL
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "postgres")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "processing_db")
    SQLALCHEMY_DATABASE_URI: Optional[str] = os.getenv(
        "DATABASE_URL",
        f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}/{POSTGRES_DB}"
    )
    
    # MongoDB
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://mongodb:27017/processing")
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    KAFKA_CONSUMER_GROUP: str = os.getenv("KAFKA_CONSUMER_GROUP", "processing-service")
    KAFKA_INPUT_TOPIC: str = os.getenv("KAFKA_INPUT_TOPIC", "raw-data")
    KAFKA_OUTPUT_TOPIC: str = os.getenv("KAFKA_OUTPUT_TOPIC", "processed-data")
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # 外部服务URLs
    STORAGE_SERVICE_URL: str = os.getenv("STORAGE_SERVICE_URL", "http://storage-service:8000/api/v1")
    SCRAPER_SERVICE_URL: str = os.getenv("SCRAPER_SERVICE_URL", "http://scraper-service:8000/api/v1")
    
    # 处理配置
    MAX_PROCESSING_TIME: int = int(os.getenv("MAX_PROCESSING_TIME", 300))  # 秒
    MAX_BATCH_SIZE: int = int(os.getenv("MAX_BATCH_SIZE", 100))
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "zh-cn")
    
    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:3000",
    ]
    
    class Config:
        case_sensitive = True

settings = Settings() 