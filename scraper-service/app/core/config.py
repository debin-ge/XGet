from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "XGet Scraper Service"
    API_V1_STR: str = "/api/v1"
    
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "postgres")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "scraper_db")
    SQLALCHEMY_DATABASE_URI: Optional[str] = os.getenv("DATABASE_URL")
    
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/2")
    REDIS_MAX_CONNECTIONS: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
    REDIS_TIMEOUT: int = int(os.getenv("REDIS_TIMEOUT", "5"))
    
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://mongodb:27017/scraper_db")
    
    ACCOUNT_SERVICE_URL: str = os.getenv("ACCOUNT_SERVICE_URL", "http://account-service:8000")
    PROXY_SERVICE_URL: str = os.getenv("PROXY_SERVICE_URL", "http://proxy-service:8000")
    
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    KAFKA_TOPIC_TASKS: str = os.getenv("KAFKA_TOPIC_TASKS", "scraper-tasks")
    KAFKA_TOPIC_CONTROL: str = os.getenv("KAFKA_TOPIC_CONTROL", "scraper-control")
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: Optional[str] = os.getenv("LOG_DIR")
    
    MAX_CONCURRENT_TASKS: int = 5
    
    # Kafka消费者配置 (aiokafka支持的参数)
    KAFKA_MAX_POLL_RECORDS: int = int(os.getenv("KAFKA_MAX_POLL_RECORDS", "10"))
    KAFKA_SESSION_TIMEOUT_MS: int = int(os.getenv("KAFKA_SESSION_TIMEOUT_MS", "30000"))
    KAFKA_HEARTBEAT_INTERVAL_MS: int = int(os.getenv("KAFKA_HEARTBEAT_INTERVAL_MS", "3000"))
    KAFKA_FETCH_MAX_WAIT_MS: int = int(os.getenv("KAFKA_FETCH_MAX_WAIT_MS", "500"))
    KAFKA_FETCH_MIN_BYTES: int = int(os.getenv("KAFKA_FETCH_MIN_BYTES", "1"))
    KAFKA_FETCH_MAX_BYTES: int = int(os.getenv("KAFKA_FETCH_MAX_BYTES", "52428800"))  # 50MB
    
    # Kafka主题配置
    KAFKA_TOPIC_PARTITIONS: int = int(os.getenv("KAFKA_TOPIC_PARTITIONS", "3"))
    KAFKA_TOPIC_RETENTION_MS: str = os.getenv("KAFKA_TOPIC_RETENTION_MS", "604800000")  # 7天
    KAFKA_TOPIC_MAX_MESSAGE_BYTES: str = os.getenv("KAFKA_TOPIC_MAX_MESSAGE_BYTES", "1048576")  # 1MB
    
    @property
    def get_database_url(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
