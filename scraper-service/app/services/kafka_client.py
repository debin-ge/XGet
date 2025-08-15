import json
import asyncio
from typing import Dict, Any, Optional
from aiokafka import AIOKafkaProducer
from ..core.config import settings
from ..core.logging import logger

class KafkaClient:
    """Kafka客户端管理类，提供连接池和重试机制"""
    
    def __init__(self):
        self._producer: Optional[AIOKafkaProducer] = None
        self._lock = asyncio.Lock()
        self._retry_count = 3
        self._retry_delay = 1.0  # 秒
        
    async def get_producer(self) -> AIOKafkaProducer:
        """获取或创建producer连接"""
        if self._producer is None:
            async with self._lock:
                if self._producer is None:
                    for attempt in range(self._retry_count):
                        try:
                            self._producer = AIOKafkaProducer(
                                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                                acks='all'  # 确保消息被所有副本确认
                            )
                            await self._producer.start()
                            logger.info("Kafka producer已启动")
                            break
                        except Exception as e:
                            logger.error(f"启动Kafka producer失败 (尝试 {attempt + 1}/{self._retry_count}): {e}")
                            if attempt < self._retry_count - 1:
                                await asyncio.sleep(self._retry_delay * (attempt + 1))
                            else:
                                raise Exception(f"Kafka producer启动最终失败: {e}")
        return self._producer
    
    async def send_message(self, topic: str, message: Dict[str, Any], retry: bool = True) -> bool:
        """发送消息到指定主题，支持重试"""
        for attempt in range(self._retry_count if retry else 1):
            try:
                producer = await self.get_producer()
                await producer.send_and_wait(topic, message)
                logger.debug(f"消息已发送到主题 {topic}")
                return True
            except Exception as e:
                logger.error(f"发送消息到主题 {topic} 失败 (尝试 {attempt + 1}/{self._retry_count}): {e}")
                if attempt < self._retry_count - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                else:
                    return False
        return False
    
    async def send_task(self, task_data: Dict[str, Any]) -> bool:
        """发送任务消息"""
        return await self.send_message(settings.KAFKA_TOPIC_TASKS, task_data)
    
    async def send_control(self, control_data: Dict[str, Any]) -> bool:
        """发送控制消息"""
        return await self.send_message(settings.KAFKA_TOPIC_CONTROL, control_data)
    
    async def close(self):
        """关闭producer连接"""
        if self._producer:
            await self._producer.stop()
            self._producer = None
            logger.info("Kafka producer已关闭")

# 全局Kafka客户端实例
kafka_client = KafkaClient() 