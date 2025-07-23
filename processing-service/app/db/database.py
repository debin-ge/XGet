from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from ..core.config import settings

# 配置日志
logger = logging.getLogger(__name__)

# SQLAlchemy配置
engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)
Base = declarative_base()

# MongoDB配置
try:
    mongo_client = AsyncIOMotorClient(settings.MONGODB_URI)
    mongo_db = mongo_client.get_database()
    logger.info("MongoDB连接成功")
except Exception as e:
    logger.error(f"MongoDB连接失败: {e}")
    mongo_client = None
    mongo_db = None

async def get_db() -> AsyncSession:
    """
    获取数据库会话
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """
    初始化数据库
    """
    try:
        async with engine.begin() as conn:
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
            logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise 