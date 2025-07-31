import asyncio
import json
from typing import Dict, Any, Optional, Set
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import httpx
from ..core.config import settings
from .twitter_scraper import TwitterScraper
from ..services.scraper_service import ScraperService
from ..db.database import async_session
from ..models.task import Task
from sqlalchemy import update
from datetime import datetime
from ..services.task_execution_service import TaskExecutionService
from ..schemas.task_execution import TaskExecutionUpdate
from ..core.logging import logger


class TaskWorker:
    def __init__(self):
        self.running = False
        self.consumer = None
        self.control_consumer = None
        self.producer = None
        self.tasks = {}  # 正在处理的任务
        self.stop_tasks = set()  # 需要停止的任务ID集合


    async def start(self):
        """启动工作器"""
        self.running = False  # 先设为False，确保重启时不会出现问题
        self.running = True
        
        # 创建Kafka消费者 - 处理任务
        self.consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC_TASKS,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="scraper-worker",
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        # 创建Kafka消费者 - 处理控制消息
        self.control_consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC_CONTROL,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="scraper-control",
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        # 创建Kafka生产者
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        await self.consumer.start()
        await self.control_consumer.start()
        await self.producer.start()
        
        # 启动控制消息处理
        asyncio.create_task(self.process_control_messages())
        
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
            await self.control_consumer.stop()
            await self.producer.stop()

    async def process_control_messages(self):
        """处理控制消息"""
        try:
            async for message in self.control_consumer:
                if not self.running:
                    break
                    
                control_data = message.value
                logger.info(f"收到控制消息: {control_data}")
                
                action = control_data.get("action")
                task_id = control_data.get("task_id")
                
                if action == "STOP_TASK" and task_id:
                    logger.info(f"收到停止任务请求: {task_id}")
                    self.stop_tasks.add(task_id)
                    
                    # 如果任务不在处理中，可能已经完成或者失败
                    if task_id not in self.tasks:
                        logger.info(f"任务 {task_id} 不在处理中，可能已经完成或者失败")
                        continue
                        
                    # 更新任务状态为已停止
                    await self.update_task_status(task_id, "STOPPED", 0.0)
        except Exception as e:
            logger.error(f"处理控制消息异常: {e}")

    async def stop(self):
        """停止工作器"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
        if self.control_consumer:
            await self.control_consumer.stop()
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
                await self.update_execution_status(task_id, "FAILED", error_msg="获取账号信息失败")
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
                await self.update_execution_status(task_id, "FAILED", error_msg="设置Twitter API失败")
                return
                
            # 根据任务类型执行不同的抓取逻辑
            results = []
            if task_type == "USER_INFO":
                username = parameters.get("username")
                if not username:
                    await self.update_task_status(task_id, "FAILED", 0.0, error_msg="缺少参数: username")
                    await self.update_execution_status(task_id, "FAILED", error_msg="缺少参数: username")
                    return
                    
                # 检查任务是否被要求停止
                if task_id in self.stop_tasks:
                    await self.update_task_status(task_id, "STOPPED", 0.0)
                    await self.update_execution_status(task_id, "STOPPED")
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
                    await self.update_execution_status(task_id, "FAILED", error_msg="缺少参数: username")
                    return
                
                tweet_count = 0
                async for tweet in scraper.get_user_tweets_stream(
                    username, 
                    limit=limit, 
                    include_replies=include_replies, 
                    include_retweets=include_retweets
                ):
                    # 检查任务是否被要求停止
                    if task_id in self.stop_tasks:
                        await self.update_task_status(task_id, "STOPPED", float(tweet_count) / limit)
                        await self.update_execution_status(task_id, "STOPPED")
                        return
                        
                    tweet.task_id = task_id
                    results.append(tweet)
                    tweet_count += 1
                    
                    # 每收集10条推文，更新一次进度
                    if tweet_count % 10 == 0:
                        progress = min(float(tweet_count) / limit, 1.0)
                        await self.update_task_status(task_id, "RUNNING", progress)
                    
            elif task_type == "SEARCH":
                query = parameters.get("query")
                limit = parameters.get("limit", 5)
                
                if not query:
                    await self.update_task_status(task_id, "FAILED", 0.0, error_msg="缺少参数: query")
                    await self.update_execution_status(task_id, "FAILED", error_msg="缺少参数: query")
                    return
                
                async for tweet in scraper.search_tweets_stream(query, limit=limit):
                    # 检查任务是否被要求停止
                    if task_id in self.stop_tasks:
                        await self.update_task_status(task_id, "STOPPED", 0.0)
                        await self.update_execution_status(task_id, "STOPPED")
                        return
                        
                    tweet.task_id = task_id
                    results.append(tweet)
                    
            elif task_type == "TOPIC":
                topic = parameters.get("topic")
                limit = parameters.get("limit", 100)
                
                if not topic:
                    await self.update_task_status(task_id, "FAILED", 0.0, error_msg="缺少参数: topic")
                    await self.update_execution_status(task_id, "FAILED", error_msg="缺少参数: topic")
                    return
                    
                tweet_count = 0
                async for tweet in scraper.get_topic_tweets_stream(topic, limit=limit):
                    # 检查任务是否被要求停止
                    if task_id in self.stop_tasks:
                        await self.update_task_status(task_id, "STOPPED", float(tweet_count) / limit)
                        await self.update_execution_status(task_id, "STOPPED")
                        return
                        
                    tweet.task_id = task_id
                    results.append(tweet)
                    tweet_count += 1
                    
                    # 每收集10条推文，更新一次进度
                    if tweet_count % 10 == 0:
                        progress = min(float(tweet_count) / limit, 1.0)
                        await self.update_task_status(task_id, "RUNNING", progress)
                    
            elif task_type == "FOLLOWERS":
                username = parameters.get("username")
                limit = parameters.get("limit", 100)
                
                if not username:
                    await self.update_task_status(task_id, "FAILED", 0.0, error_msg="缺少参数: username")
                    await self.update_execution_status(task_id, "FAILED", error_msg="缺少参数: username")
                    return
                    
                follower_count = 0
                async for follower in scraper.get_followers_stream(username, limit=limit):
                    # 检查任务是否被要求停止
                    if task_id in self.stop_tasks:
                        await self.update_task_status(task_id, "STOPPED", float(follower_count) / limit)
                        await self.update_execution_status(task_id, "STOPPED")
                        return
                        
                    follower.task_id = task_id
                    results.append(follower)
                    follower_count += 1
                    
                    # 每收集10个关注者，更新一次进度
                    if follower_count % 10 == 0:
                        progress = min(float(follower_count) / limit, 1.0)
                        await self.update_task_status(task_id, "RUNNING", progress)
            else:
                await self.update_task_status(task_id, "FAILED", 0.0, error_msg=f"不支持的任务类型: {task_type}")
                await self.update_execution_status(task_id, "FAILED", error_msg=f"不支持的任务类型: {task_type}")
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
                await self.update_execution_status(task_id, "COMPLETED")
            else:
                # 没有结果，但任务完成
                await self.update_task_status(
                    task_id, 
                    "COMPLETED", 
                    1.0, 
                    result_count=0
                )
                await self.update_execution_status(task_id, "COMPLETED")
                
        except Exception as e:
            logger.error(f"处理任务异常: {task_id} - {e}")
            await self.update_task_status(task_id, "FAILED", 0.0, error_msg=str(e))
            await self.update_execution_status(task_id, "FAILED", error_msg=str(e))
        finally:
            # 从正在处理的任务和停止任务集合中移除
            if task_id in self.tasks:
                del self.tasks[task_id]
            if task_id in self.stop_tasks:
                self.stop_tasks.remove(task_id)

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
            # 创建数据库会话
            session = await async_session()
            try:
                update_data = {
                    "status": status,
                    "progress": progress,
                    "updated_at": datetime.now()
                }
                
                if result_count > 0:
                    update_data["result_count"] = result_count
                    
                if error_msg:
                    # 截断错误信息，防止超出数据库字段长度
                    if len(error_msg) > 500:
                        error_msg = error_msg[:497] + "..."
                    update_data["error_message"] = error_msg
                
                # 如果状态变为RUNNING，设置started_at
                if status == "RUNNING":
                    update_data["started_at"] = datetime.now()
                    
                # 如果状态变为COMPLETED或FAILED，设置completed_at
                if status in ["COMPLETED", "FAILED", "STOPPED"]:
                    update_data["completed_at"] = datetime.now()
                
                await session.execute(
                    update(Task)
                    .where(Task.id == task_id)
                    .values(**update_data)
                )
                await session.commit()
                logger.info(f"任务状态已更新: {task_id} - {status} - {progress}")
            finally:
                await session.close()
        except Exception as e:
            logger.error(f"更新任务状态失败: {task_id} - {e}")

    async def get_account_info(self, account_id: str) -> Optional[Dict]:
        """获取账号信息"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.ACCOUNT_SERVICE_URL}{settings.API_V1_STR}/accounts/{account_id}"
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
                    f"{settings.PROXY_SERVICE_URL}{settings.API_V1_STR}/proxies/{proxy_id}"
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"获取代理信息失败: {proxy_id} - {e}")
        return None

    async def update_execution_status(self, task_id: str, status: str, error_msg: Optional[str] = None):
        """更新任务执行记录状态"""
        try:
            # 创建数据库会话
            session = await async_session()
            try:
                execution_service = TaskExecutionService(session)
                executions = await execution_service.get_executions_by_task(task_id)
                if executions:
                    latest_execution = executions[0]  # 最新的执行记录
                    await execution_service.update_execution(
                        latest_execution.id,
                        TaskExecutionUpdate(
                            status=status,
                            completed_at=datetime.now(),
                            error_message=error_msg
                        )
                    )
            finally:
                await session.close()
        except Exception as e:
            logger.error(f"更新任务执行记录状态失败: {task_id} - {e}")


task_worker = TaskWorker()
