from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from minio import Minio
from elasticsearch import AsyncElasticsearch
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

# MinIO配置
try:
    minio_client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        secure=settings.MINIO_SECURE
    )
    # 确保默认存储桶存在
    if not minio_client.bucket_exists(settings.DEFAULT_BUCKET):
        minio_client.make_bucket(settings.DEFAULT_BUCKET)
        logger.info(f"创建MinIO存储桶: {settings.DEFAULT_BUCKET}")
    logger.info("MinIO连接成功")
except Exception as e:
    logger.error(f"MinIO连接失败: {e}")
    minio_client = None

# Elasticsearch配置
es_client = None
try:
    es_kwargs = {
        "hosts": [f"http://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"]
    }
    if settings.ELASTICSEARCH_USERNAME and settings.ELASTICSEARCH_PASSWORD:
        es_kwargs["basic_auth"] = (settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD)
    
    es_client = AsyncElasticsearch(**es_kwargs)
    logger.info("Elasticsearch连接成功")
except Exception as e:
    logger.error(f"Elasticsearch连接失败: {e}")
    es_client = None

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