import asyncio
import json
import logging
from typing import Dict, Any, Optional
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import httpx
from ..core.config import settings
from ..schemas.task import TaskUpdate
from ..schemas.result import ResultCreate
from .twitter_scraper import TwitterScraper
from ..services.scraper_service import ScraperService

logger = logging.getLogger(__name__)


class TaskWorker:
    def __init__(self):
        self.running = False
        self.consumer = None
        self.producer = None
        self.tasks = {}  # 正在处理的任务

    async def start(self):
        """启动工作器"""
        self.running = True
        
        # 创建Kafka消费者
        self.consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC_TASKS,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="scraper-worker",
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        # 创建Kafka生产者
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        await self.consumer.start()
        await self.producer.start()
        
        try:
            async for message in self.consumer:
                if not self.running:
                    break
                    
                task_data = message.value
                logger.info(f"收到任务: {task_data}")
                
                # 检查是否已经达到最大并发任务数
                if len(self.tasks) >= settings.MAX_CONCURRENT_TASKS:
                    logger.warning(f"已达到最大并发任务数: {settings.MAX_CONCURRENT_TASKS}")
                    continue
                    
                # 异步处理任务
                task_id = task_data.get("task_id")
                if task_id:
                    self.tasks[task_id] = task_data
                    asyncio.create_task(self.process_task(task_data))
        finally:
            await self.consumer.stop()
            await self.producer.stop()

    async def stop(self):
        """停止工作器"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
        if self.producer:
            await self.producer.stop()

    async def process_task(self, task_data: Dict[str, Any]):
        """处理任务"""
        task_id = task_data.get("task_id")
        task_type = task_data.get("task_type")
        parameters = task_data.get("parameters", {})
        account_id = task_data.get("account_id")
        proxy_id = task_data.get("proxy_id")
        
        try:
            # 更新任务状态为运行中
            await self.update_task_status(task_id, "RUNNING", 0.0)
            
            # 获取账号信息
            account_info = await self.get_account_info(account_id)
            if not account_info:
                await self.update_task_status(task_id, "FAILED", 0.0, error_msg="获取账号信息失败")
                return
                
            # 获取代理信息
            proxy_info = None
            if proxy_id:
                proxy_info = await self.get_proxy_info(proxy_id)
                
            # 创建Twitter抓取器
            scraper = TwitterScraper(account_info, proxy_info)
            
            # 设置Twitter API
            setup_success = await scraper.setup()
            if not setup_success:
                await self.update_task_status(task_id, "FAILED", 0.0, error_msg="设置Twitter API失败")
                return
                
            # 根据任务类型执行不同的抓取逻辑
            results = []
            if task_type == "USER_INFO":
                username = parameters.get("username")
                if not username:
                    await self.update_task_status(task_id, "FAILED", 0.0, error_msg="缺少参数: username")
                    return
                    
                result = await scraper.get_user_info(username)
                if result:
                    result.task_id = task_id
                    results.append(result)
                    
            elif task_type == "USER_TWEETS":
                username = parameters.get("username")
                limit = parameters.get("limit", 100)
                include_replies = parameters.get("include_replies", False)
                include_retweets = parameters.get("include_retweets", False)
                
                if not username:
                    await self.update_task_status(task_id, "FAILED", 0.0, error_msg="缺少参数: username")
                    return
                    
                tweet_results = await scraper.get_user_tweets(
                    username, 
                    limit=limit, 
                    include_replies=include_replies, 
                    include_retweets=include_retweets
                )
                
                for result in tweet_results:
                    result.task_id = task_id
                    results.append(result)
                    
            elif task_type == "SEARCH":
                query = parameters.get("query")
                limit = parameters.get("limit", 100)
                
                if not query:
                    await self.update_task_status(task_id, "FAILED", 0.0, error_msg="缺少参数: query")
                    return
                    
                tweet_results = await scraper.search_tweets(query, limit=limit)
                
                for result in tweet_results:
                    result.task_id = task_id
                    results.append(result)
                    
            elif task_type == "TOPIC":
                topic = parameters.get("topic")
                limit = parameters.get("limit", 100)
                
                if not topic:
                    await self.update_task_status(task_id, "FAILED", 0.0, error_msg="缺少参数: topic")
                    return
                    
                tweet_results = await scraper.get_topic_tweets(topic, limit=limit)
                
                for result in tweet_results:
                    result.task_id = task_id
                    results.append(result)
                    
            elif task_type == "FOLLOWERS":
                username = parameters.get("username")
                limit = parameters.get("limit", 100)
                
                if not username:
                    await self.update_task_status(task_id, "FAILED", 0.0, error_msg="缺少参数: username")
                    return
                    
                follower_results = await scraper.get_followers(username, limit=limit)
                
                for result in follower_results:
                    result.task_id = task_id
                    results.append(result)
            else:
                await self.update_task_status(task_id, "FAILED", 0.0, error_msg=f"不支持的任务类型: {task_type}")
                return
                
            # 保存结果
            if results:
                scraper_service = ScraperService()
                saved_results = await scraper_service.save_results(results)
                
                # 更新任务状态
                await self.update_task_status(
                    task_id, 
                    "COMPLETED", 
                    1.0, 
                    result_count=len(saved_results)
                )
            else:
                # 没有结果，但任务完成
                await self.update_task_status(
                    task_id, 
                    "COMPLETED", 
                    1.0, 
                    result_count=0
                )
                
            # 关闭Twitter API
            await scraper.close()
                
        except Exception as e:
            logger.error(f"处理任务异常: {task_id} - {e}")
            await self.update_task_status(task_id, "FAILED", 0.0, error_msg=str(e))
        finally:
            # 从正在处理的任务中移除
            if task_id in self.tasks:
                del self.tasks[task_id]

    async def update_task_status(
        self, 
        task_id: str, 
        status: str, 
        progress: float, 
        result_count: int = 0, 
        error_msg: Optional[str] = None
    ):
        """更新任务状态"""
        try:
            async with httpx.AsyncClient() as client:
                update_data = {
                    "status": status,
                    "progress": progress
                }
                
                if result_count > 0:
                    update_data["result_count"] = result_count
                    
                if error_msg:
                    update_data["error_msg"] = error_msg
                    
                await client.put(
                    f"{settings.API_V1_STR}/tasks/{task_id}",
                    json=update_data
                )
        except Exception as e:
            logger.error(f"更新任务状态失败: {task_id} - {e}")

    async def get_account_info(self, account_id: str) -> Optional[Dict]:
        """获取账号信息"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.ACCOUNT_SERVICE_URL}/accounts/{account_id}"
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"获取账号信息失败: {account_id} - {e}")
        return None

    async def get_proxy_info(self, proxy_id: str) -> Optional[Dict]:
        """获取代理信息"""
        if not proxy_id:
            return None
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.PROXY_SERVICE_URL}/proxies/{proxy_id}"
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"获取代理信息失败: {proxy_id} - {e}")
        return None


task_worker = TaskWorker()
