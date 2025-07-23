import json
import logging
import asyncio
from aiokafka import AIOKafkaConsumer
from ..core.config import settings
from ..services.processing_service import ProcessingService

logger = logging.getLogger(__name__)

# 全局消费者实例
consumer = None

async def process_message(message):
    """
    处理从Kafka接收的消息
    """
    try:
        # 解析消息内容
        data = json.loads(message.value.decode("utf-8"))
        logger.info(f"接收到消息: {data.get('id', 'unknown')}")
        
        # 创建处理服务实例
        processing_service = ProcessingService()
        
        # 根据消息类型进行处理
        message_type = data.get("type", "unknown")
        if message_type == "raw_data":
            # 处理原始数据
            result = await processing_service.process_raw_data(data)
        elif message_type == "processing_request":
            # 处理特定处理请求
            result = await processing_service.process_request(data)
        else:
            logger.warning(f"未知消息类型: {message_type}")
            return
        
        logger.info(f"消息处理完成: {data.get('id', 'unknown')}")
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
        
        # 消费消息
        try:
            async for message in consumer:
                await process_message(message)
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