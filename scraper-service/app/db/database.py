from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import motor.motor_asyncio
from ..core.config import settings

# PostgreSQL 连接
DATABASE_URL = settings.get_database_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# MongoDB 连接
try:
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
    mongodb = mongo_client.get_database()
except Exception as e:
    import logging
    logging.error(f"MongoDB连接失败: {str(e)}")
    # 创建一个空的MongoDB客户端，避免启动失败
    mongodb = None

async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
