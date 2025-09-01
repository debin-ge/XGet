import asyncio
import json
from typing import Dict, Any, Optional
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from ..core.config import settings
from .twitter_scraper import TwitterScraper
from ..services.scraper_service import ScraperService
from ..models.task import Task
from sqlalchemy import update
from datetime import datetime
from ..services.task_execution_service import TaskExecutionService
from ..schemas.task_execution import TaskExecutionUpdate
from ..core.logging import logger
from ..services.proxy_client import ProxyClient
from ..services.account_client import AccountClient
from ..db.database import get_db


class TaskWorker:
    def __init__(self):
        self.running = False
        self.consumer = None
        self.control_consumer = None
        self.producer = None
        self.tasks = {}  # 正在处理的任务
        self.stop_tasks = set()  # 需要停止的任务ID集合
        self.proxy_client = ProxyClient()  # 代理客户端
        self.account_client = AccountClient()  # 账号客户端
        self.control_task = None  # 控制消息处理任务
        self.task_futures = {}  # 任务Future对象，用于跟踪和取消

    async def start(self):
        """启动工作器"""
        self.running = False  # 先设为False，确保重启时不会出现问题
        self.running = True
        
        # Kafka连接重试机制
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # 创建Kafka消费者 - 处理任务
                self.consumer = AIOKafkaConsumer(
                    settings.KAFKA_TOPIC_TASKS,
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    group_id="scraper-worker",
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    auto_offset_reset='earliest',  # 从最早的消息开始消费
                    enable_auto_commit=False,  # 手动提交偏移量
                    max_poll_records=settings.KAFKA_MAX_POLL_RECORDS,  # 每次最多拉取的消息数
                    session_timeout_ms=settings.KAFKA_SESSION_TIMEOUT_MS,  # 会话超时时间
                    heartbeat_interval_ms=settings.KAFKA_HEARTBEAT_INTERVAL_MS,  # 心跳间隔
                    fetch_max_wait_ms=settings.KAFKA_FETCH_MAX_WAIT_MS,
                    fetch_min_bytes=settings.KAFKA_FETCH_MIN_BYTES,
                    fetch_max_bytes=settings.KAFKA_FETCH_MAX_BYTES
                )
                
                # 创建Kafka消费者 - 处理控制消息
                self.control_consumer = AIOKafkaConsumer(
                    settings.KAFKA_TOPIC_CONTROL,
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    group_id="scraper-control",
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    # 控制消息需要实时处理
                    auto_offset_reset='latest',
                    enable_auto_commit=True,
                    max_poll_records=1
                )
                
                # 创建Kafka生产者
                self.producer = AIOKafkaProducer(
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    acks='all'  # 确保消息被所有副本确认
                )
                
                await self.consumer.start()
                await self.control_consumer.start()
                await self.producer.start()
                
                logger.info("Kafka连接成功，工作器已启动")
                break  # 成功连接，跳出重试循环
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Kafka连接失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    logger.error(f"Kafka连接最终失败: {str(e)}")
                    logger.warning("工作器启动失败，Kafka功能不可用")
                    return  # 退出启动流程
        
        # 启动控制消息处理
        self.control_task = asyncio.create_task(self.process_control_messages())
        
        try:
            async for message in self.consumer:
                if not self.running:
                    break
                    
                task_data = message.value
                logger.info(f"收到任务: {task_data}")
                
                # 检查是否已经达到最大并发任务数
                if len(self.tasks) >= settings.MAX_CONCURRENT_TASKS:
                    logger.warning(f"已达到最大并发任务数: {settings.MAX_CONCURRENT_TASKS}")
                    # 即使达到最大并发数，也要确认消息已处理
                    await self.consumer.commit()
                    continue
                    
                # 异步处理任务
                task_id = task_data.get("task_id")
                if task_id:
                    self.tasks[task_id] = task_data
                    # 创建任务并跟踪Future对象
                    future = asyncio.create_task(self.process_task(task_data))
                    self.task_futures[task_id] = future
                    
                    # 添加异常处理回调
                    def task_done_callback(task_future, tid=task_id):
                        try:
                            task_future.result()  # 获取结果，如果有异常会抛出
                        except Exception as e:
                            logger.error(f"任务 {tid} 执行过程中发生未捕获的异常: {e}")
                        finally:
                            # 清理任务记录
                            self.tasks.pop(tid, None)
                            self.task_futures.pop(tid, None)
                            self.stop_tasks.discard(tid)
                    
                    future.add_done_callback(lambda f: task_done_callback(f, task_id))
                    
                # 手动提交偏移量，确保消息被确认
                await self.consumer.commit()
        finally:
            # 清理资源
            await self._cleanup_resources()

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
                    await self.update_task_status(task_id, "STOPPED")
        except Exception as e:
            logger.error(f"处理控制消息异常: {e}")

    async def _cleanup_resources(self):
        """清理资源"""
        # 取消所有正在运行的任务
        for task_id, future in list(self.task_futures.items()):
            if not future.done():
                logger.info(f"取消任务: {task_id}")
                future.cancel()
                try:
                    await future
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"取消任务 {task_id} 时发生异常: {e}")
        
        # 取消控制消息处理任务
        if self.control_task and not self.control_task.done():
            self.control_task.cancel()
            try:
                await self.control_task
            except asyncio.CancelledError:
                pass
        
        # 关闭Kafka连接
        try:
            if self.consumer:
                await self.consumer.stop()
        except Exception as e:
            logger.error(f"关闭consumer失败: {e}")
            
        try:
            if self.control_consumer:
                await self.control_consumer.stop()
        except Exception as e:
            logger.error(f"关闭control_consumer失败: {e}")
            
        try:
            if self.producer:
                await self.producer.stop()
        except Exception as e:
            logger.error(f"关闭producer失败: {e}")

    async def stop(self):
        """停止工作器"""
        logger.info("正在停止工作器...")
        self.running = False
        await self._cleanup_resources()
        logger.info("工作器已停止")

    async def process_task(self, task_data: Dict[str, Any]):
        """处理任务"""
        task_id = task_data.get("task_id")
        task_type = task_data.get("task_type")
        parameters = task_data.get("parameters", {})
        account_id = task_data.get("account_id")
        proxy_id = task_data.get("proxy_id")
        scraper = None
        
        try:
            # 更新任务状态为运行中
            await self.update_task_status(task_id, "RUNNING")
            
            # 获取账号信息
            account_info = await self.account_client.get_account(account_id)
            if not account_info:
                await self.update_task_status(task_id, "FAILED", error_msg="获取账号信息失败")
                await self.update_execution_status(task_id, "FAILED", error_msg="获取账号信息失败")
                return
                            
            # 获取代理信息
            proxy_info = None
            if proxy_id:
                proxy_info = await self.proxy_client.get_proxy(proxy_id)
            
            logger.info(f"获取用户信息为：{account_info}")

            # 创建Twitter抓取器
            scraper = TwitterScraper(account_info, proxy_info)
            
            # 设置Twitter API
            setup_success = await scraper.setup()
            if not setup_success:
                await self.update_task_status(task_id, "FAILED", error_msg="设置Twitter API失败")
                await self.update_execution_status(task_id, "FAILED", error_msg="设置Twitter API失败")
                
                # 记录代理使用失败
                if proxy_id and proxy_info:
                    await self.proxy_client.record_proxy_usage(
                        proxy_id=proxy_id,
                        success="FAILED",
                        task_id=task_id,
                        account_id=account_id,
                        service_name=settings.PROJECT_NAME,
                        response_time=None,
                        proxy_ip=proxy_info.get("ip"),
                        proxy_port=proxy_info.get("port"),
                        account_username_email=account_info.get("username") or account_info.get("email"),
                        task_name=task_data.get("task_name",None),
                        quality_score=proxy_info.get("quality_score"),
                        latency=proxy_info.get("latency")
                    )
                    
                return
                
            # 根据任务类型执行不同的抓取逻辑
            results = []
            task_success = "SUCCESS"
            
            if task_type == "USER_INFO":
                username = parameters.get("username")
                if not username:
                    await self.update_task_status(task_id, "FAILED", error_msg="缺少参数: username")
                    await self.update_execution_status(task_id, "FAILED", error_msg="缺少参数: username")
                    return
                    
                # 检查任务是否被要求停止
                if task_id in self.stop_tasks:
                    await self.update_task_status(task_id, "STOPPED")
                    await self.update_execution_status(task_id, "STOPPED")
                    return
                    
                result = await scraper.get_user_info(username)
                if result:
                    result.task_id = task_id
                    results.append(result)
                
            elif task_type == "USER_TWEETS":
                uid = parameters.get("uid")
                limit = parameters.get("limit", 10)
                include_replies = parameters.get("include_replies", False)
                
                if not uid:
                    await self.update_task_status(task_id, "FAILED", error_msg="缺少参数: uid")
                    await self.update_execution_status(task_id, "FAILED", error_msg="缺少参数: uid")
                    return
            
                try:
                    async for tweet in scraper.get_user_tweets_stream(
                        uid, 
                        limit=limit, 
                        include_replies=include_replies, 
                    ):
                        # 检查任务是否被要求停止
                        if task_id in self.stop_tasks:
                            await self.update_task_status(task_id, "STOPPED")
                            await self.update_execution_status(task_id, "STOPPED")
                            return
                            
                        tweet.task_id = task_id
                        results.append(tweet)
                except Exception as e:
                    logger.error(f"获取用户推文时发生异常: {e}")
                    raise
                    
            elif task_type == "SEARCH":
                query = parameters.get("query")
                limit = parameters.get("limit", 10)
                
                if not query:
                    await self.update_task_status(task_id, "FAILED", error_msg="缺少参数: query")
                    await self.update_execution_status(task_id, "FAILED", error_msg="缺少参数: query")
                    return
                
                try:
                    async for tweet in scraper.search_tweets_stream(query, limit=limit):
                        # 检查任务是否被要求停止
                        if task_id in self.stop_tasks:
                            await self.update_task_status(task_id, "STOPPED")
                            await self.update_execution_status(task_id, "STOPPED")
                            return
                            
                        tweet.task_id = task_id
                        results.append(tweet)
                except Exception as e:
                    logger.error(f"搜索推文时发生异常: {e}")
                    raise
                    
            elif task_type == "TOPIC":
                topic = parameters.get("topic")
                limit = parameters.get("limit", 10)
                
                if not topic:
                    await self.update_task_status(task_id, "FAILED", error_msg="缺少参数: topic")
                    await self.update_execution_status(task_id, "FAILED", error_msg="缺少参数: topic")
                    return
                    
                try:
                    async for tweet in scraper.get_topic_tweets_stream(topic, limit=limit):
                        # 检查任务是否被要求停止
                        if task_id in self.stop_tasks:
                            await self.update_task_status(task_id, "STOPPED")
                            await self.update_execution_status(task_id, "STOPPED")
                            return
                            
                        tweet.task_id = task_id
                        results.append(tweet)
                except Exception as e:
                    logger.error(f"获取话题推文时发生异常: {e}")
                    raise
                    
            elif task_type == "FOLLOWERS":
                uid = parameters.get("uid")
                limit = parameters.get("limit", 10)
                
                if not uid:
                    await self.update_task_status(task_id, "FAILED", error_msg="缺少参数: uid")
                    await self.update_execution_status(task_id, "FAILED", error_msg="缺少参数: uid")
                    return
                    
                try:
                    async for follower in scraper.get_followers_stream(uid, limit=limit):
                        # 检查任务是否被要求停止
                        if task_id in self.stop_tasks:
                            await self.update_task_status(task_id, "STOPPED")
                            await self.update_execution_status(task_id, "STOPPED")
                            return
                            
                        follower.task_id = task_id
                        results.append(follower)
                except Exception as e:
                    logger.error(f"获取用户粉丝时发生异常: {e}")
                    raise
                    
            elif task_type == "FOLLOWING":
                uid = parameters.get("uid")
                limit = parameters.get("limit", 10)
                
                if not uid:
                    await self.update_task_status(task_id, "FAILED", error_msg="缺少参数: uid")
                    await self.update_execution_status(task_id, "FAILED", error_msg="缺少参数: uid")
                    return
                    
                try:
                    async for following in scraper.get_following_stream(uid, limit=limit):
                        # 检查任务是否被要求停止
                        if task_id in self.stop_tasks:
                            await self.update_task_status(task_id, "STOPPED")
                            await self.update_execution_status(task_id, "STOPPED")
                            return
                            
                        following.task_id = task_id
                        results.append(following)
                except Exception as e:
                    logger.error(f"获取用户关注列表时发生异常: {e}")
                    raise

            else:
                await self.update_task_status(task_id, "FAILED", error_msg=f"不支持的任务类型: {task_type}")
                await self.update_execution_status(task_id, "FAILED", error_msg=f"不支持的任务类型: {task_type}")
                return
                
            logger.info(f"获取推文结果为: {results}")
            # 保存结果
            if len(results) > 0:
                scraper_service = ScraperService()
                saved_results = await scraper_service.save_results(results)
                
                # 更新任务状态
                await self.update_task_status(
                    task_id, 
                    "COMPLETED"
                )
                await self.update_execution_status(task_id, "COMPLETED")
            else:
                # 没有结果，但任务完成
                await self.update_task_status(
                    task_id, 
                    "COMPLETED"
                )
                await self.update_execution_status(task_id, "COMPLETED")
                
                
        except Exception as e:
            logger.error(f"处理任务异常: {task_id} - {e}")
            await self.update_task_status(task_id, "FAILED", error_msg=str(e))
            await self.update_execution_status(task_id, "FAILED", error_msg=str(e))
            task_success = "FAILED"
            
        finally:
            # 清理Twitter Scraper资源
            if scraper:
                try:
                    await scraper.cleanup()
                except Exception as e:
                    logger.warning(f"清理Twitter Scraper资源失败: {e}")
                    
            # 记录代理使用
            if proxy_id and proxy_info:
                await self.proxy_client.record_proxy_usage(
                    proxy_id=proxy_id,
                    success=task_success,
                    task_id=task_id,
                    account_id=account_id,
                    service_name=settings.PROJECT_NAME,
                    response_time=None,
                    proxy_ip=proxy_info.get("ip"),
                    proxy_port=proxy_info.get("port"),
                    account_username_email=account_info.get("username") or account_info.get("email"),
                    task_name=task_data.get("task_name",None),
                    quality_score=proxy_info.get("quality_score"),
                    latency=proxy_info.get("latency")
                )
                

    async def update_task_status(
        self, 
        task_id: str, 
        status: str, 
        error_msg: Optional[str] = None
    ):
        """更新任务状态"""
        db_gen = get_db()
        db = await db_gen.__anext__()
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now()
            }
                
            if error_msg:
                # 截断错误信息，防止超出数据库字段长度
                if len(error_msg) > 500:
                    error_msg = error_msg[:497] + "..."
                update_data["error_message"] = error_msg
            
            await db.execute(
                update(Task)
                .where(Task.id == task_id)
                .values(**update_data)
            )
            await db.commit()
            logger.info(f"任务状态已更新: {task_id} - {status}")
        except Exception as e:
            logger.error(f"更新任务状态失败: {task_id} - {e}")
            await db.rollback()
        finally:
            await db.close()

    async def update_execution_status(self, task_id: str, status: str, error_msg: Optional[str] = None):
        """更新任务执行记录状态"""
        db_gen = get_db()
        db = await db_gen.__anext__()
        try:
            execution_service = TaskExecutionService(db)
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
                await db.commit()
        except Exception as e:
            logger.error(f"更新任务执行记录状态失败: {task_id} - {e}")
            await db.rollback()
        finally:
            await db.close()


task_worker = TaskWorker()
