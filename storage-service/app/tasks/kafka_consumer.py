import json
import logging
import asyncio
from typing import Dict, Any
from aiokafka import AIOKafkaConsumer
from ..core.config import settings
from ..services.storage_service import StorageService
from ..schemas.storage import StorageRequest, StorageOptions

logger = logging.getLogger(__name__)

# 全局消费者实例
consumer = None

async def process_message(message, db_pool):
    """
    处理从Kafka接收到的消息
    
    Args:
        message: Kafka消息
        db_pool: 数据库连接池
    """
    try:
        # 解析消息内容
        data = json.loads(message.value.decode("utf-8"))
        message_id = data.get("id", "unknown")
        logger.info(f"接收到消息: {message_id}")
        
        # 获取数据类型
        data_type = data.get("type", "unknown")
        
        # 获取数据内容
        content = data.get("content", {})
        if not content:
            logger.warning(f"消息 {message_id} 没有内容")
            return
        
        # 获取元数据
        metadata = data.get("metadata", {})
        
        # 获取存储选项
        storage_options = data.get("storage_options", {})
        options = StorageOptions(
            compression=storage_options.get("compression", True),
            encryption=storage_options.get("encryption", False),
            replication=storage_options.get("replication", 1)
        )
        
        # 创建存储请求
        storage_request = StorageRequest(
            data_type=data_type,
            content=content,
            metadata=metadata,
            storage_options=options
        )
        
        # 获取存储后端
        backend = data.get("backend", "S3")
        
        # 获取数据库连接
        async with db_pool() as db:
            # 创建存储服务
            storage_service = StorageService()
            
            # 存储数据
            result = await storage_service.store_data(db, storage_request, backend)
            
            logger.info(f"消息 {message_id} 处理完成，存储ID: {result.get('id')}")
            
            # 如果有回调URL，可以在这里处理
            callback_url = data.get("callback_url")
            if callback_url:
                # 实现回调逻辑
                pass
    except json.JSONDecodeError:
        logger.error("消息格式无效，无法解析JSON")
    except Exception as e:
        logger.error(f"处理消息时出错: {str(e)}", exc_info=True)

async def consume():
    """
    消费Kafka消息的主循环
    """
    global consumer
    
    try:
        # 创建Kafka消费者
        consumer = AIOKafkaConsumer(
            settings.KAFKA_INPUT_TOPIC,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=settings.KAFKA_CONSUMER_GROUP,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        )
        
        # 启动消费者
        await consumer.start()
        logger.info(f"Kafka消费者已启动，正在监听主题: {settings.KAFKA_INPUT_TOPIC}")
        
        # 获取数据库连接池
        from ..db.database import async_session
        
        # 消费消息
        try:
            async for message in consumer:
                await process_message(message, async_session)
                # 手动提交偏移量
                await consumer.commit()
        finally:
            # 确保消费者被关闭
            await consumer.stop()
    except Exception as e:
        logger.error(f"Kafka消费者错误: {str(e)}", exc_info=True)
        if consumer:
            await consumer.stop()

async def start_kafka_consumer():
    """
    启动Kafka消费者
    """
    # 在后台任务中启动消费者
    asyncio.create_task(consume())
    logger.info("Kafka消费者任务已创建") 