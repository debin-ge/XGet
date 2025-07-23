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
    
    ACCOUNT_SERVICE_URL: str = "http://account-service:8000/api/v1"
    PROXY_SERVICE_URL: str = "http://proxy-service:8000/api/v1"
    
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_TOPIC_TASKS: str = "scraper-tasks"
    KAFKA_TOPIC_RESULTS: str = "scraper-results"
    
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
