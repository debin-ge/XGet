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
    
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://mongodb:27017/scraper_db")
    
    ACCOUNT_SERVICE_URL: str = os.getenv("ACCOUNT_SERVICE_URL", "http://account-service:8000")
    PROXY_SERVICE_URL: str = os.getenv("PROXY_SERVICE_URL", "http://proxy-service:8000")
    
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    KAFKA_TOPIC_TASKS: str = os.getenv("KAFKA_TOPIC_TASKS", "scraper-tasks")
    KAFKA_TOPIC_RESULTS: str = os.getenv("KAFKA_TOPIC_RESULTS", "scraper-results")
    KAFKA_TOPIC_CONTROL: str = os.getenv("KAFKA_TOPIC_CONTROL", "scraper-control")
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: Optional[str] = os.getenv("LOG_DIR")
    
    MAX_CONCURRENT_TASKS: int = 5
    
    @property
    def get_database_url(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
