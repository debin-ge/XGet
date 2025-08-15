from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.router import api_router
from .core.config import settings
from .core.logging import initialize_logging, logger
import asyncio
from contextlib import asynccontextmanager
from .db.database import engine, Base
from .tasks.worker import task_worker

# 初始化日志系统
initialize_logging(
    log_level=settings.LOG_LEVEL,
    log_dir=settings.LOG_DIR
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时的初始化
    logger.info("服务启动中...")
    
    try:
        # 创建数据库表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # 确保Kafka主题存在
        kafka_success = await setup_kafka_topics()
        if not kafka_success:
            logger.warning("Kafka主题设置失败，但服务将继续启动")
        
        # 启动任务工作器
        worker_task = None
        try:
            worker_task = asyncio.create_task(task_worker.start())
            logger.info("任务工作器已启动")
        except Exception as e:
            logger.error(f"启动任务工作器失败: {e}")
            
        logger.info("服务启动完成")
        
        yield
        
        # 关闭时的清理
        logger.info("服务关闭中...")
        
        # 停止任务工作器
        try:
            await task_worker.stop()
            if worker_task and not worker_task.done():
                worker_task.cancel()
                try:
                    await worker_task
                except asyncio.CancelledError:
                    pass
        except Exception as e:
            logger.error(f"停止任务工作器失败: {e}")
        
        # 关闭Kafka客户端连接
        try:
            from .services.kafka_client import kafka_client
            await kafka_client.close()
        except Exception as e:
            logger.error(f"关闭Kafka客户端失败: {e}")
        
        # 关闭数据库连接
        try:
            await engine.dispose()
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}")
            
        logger.info("服务已关闭")
        
    except Exception as e:
        logger.error(f"服务启动/关闭过程中发生异常: {e}")
        raise

async def setup_kafka_topics() -> bool:
    """设置Kafka主题"""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            from aiokafka.admin import AIOKafkaAdminClient, NewTopic
            admin_client = AIOKafkaAdminClient(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
            )
            await admin_client.start()
            try:
                # 获取现有主题列表
                topics = await admin_client.list_topics()
                
                # 需要创建的主题列表
                required_topics = [
                    settings.KAFKA_TOPIC_TASKS,
                    settings.KAFKA_TOPIC_CONTROL
                ]
                
                # 检查并创建不存在的主题
                topics_to_create = []
                for topic in required_topics:
                    if topic not in topics:
                        topics_to_create.append(
                            NewTopic(
                                name=topic,
                                num_partitions=settings.KAFKA_TOPIC_PARTITIONS,
                                replication_factor=1,
                                topic_configs={
                                    'retention.ms': settings.KAFKA_TOPIC_RETENTION_MS,
                                    'cleanup.policy': 'delete',
                                    'max.message.bytes': settings.KAFKA_TOPIC_MAX_MESSAGE_BYTES
                                }
                            )
                        )
                
                if topics_to_create:
                    await admin_client.create_topics(topics_to_create)
                    logger.info(f"已创建Kafka主题: {[t.name for t in topics_to_create]}")
                else:
                    logger.info("所有Kafka主题已存在")
                return True
            finally:
                await admin_client.close()
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Kafka连接失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
            else:
                logger.error(f"Kafka连接最终失败: {str(e)}")
                return False
    return False

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 添加一个临时的根路径端点
@app.get("/")
async def root():
    return {"message": "XGet Scraper Service - Temporary Mode"}

# 添加一个临时的API版本端点
@app.get(f"{settings.API_V1_STR}")
async def api_root():
    return {
        "version": "1.0",
        "status": "maintenance",
        "message": "服务正在维护中，MongoDB依赖问题正在解决"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
