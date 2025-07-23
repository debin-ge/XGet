import asyncio
import json
import logging
from typing import Dict, Any, Optional
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import httpx
from ..core.config import settings
from ..schemas.task import TaskUpdate
from ..schemas.result import ResultCreate
from ..tasks.twitter_scraper import TwitterScraper
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
                    
                response = await client.put(
                    f"{settings.API_V1_STR}/tasks/{task_id}",
                    json=update_data
                )
                if response.status_code != 200:
                    logger.error(f"更新任务状态失败: {task_id} - {response.text}")
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
                logger.error(f"获取账号信息失败: {account_id} - 状态码: {response.status_code}")
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
                logger.error(f"获取代理信息失败: {proxy_id} - 状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"获取代理信息失败: {proxy_id} - {e}")
        return None


# 创建全局工作器实例
task_worker = TaskWorker()

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

from ..db.database import get_db
from ..schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskStatusResponse
from ..schemas.result import ResultQuery, ResultsResponse
from ..services.task_service import TaskService
from ..services.scraper_service import ScraperService

router = APIRouter()

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate, 
    db: AsyncSession = Depends(get_db)
):
    """创建采集任务"""
    service = TaskService(db)
    return await service.create_task(task)

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取任务列表"""
    service = TaskService(db)
    return await service.get_tasks(skip, limit, status, task_type)

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """获取任务详情"""
    service = TaskService(db)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str, 
    task_data: TaskUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """更新任务信息"""
    service = TaskService(db)
    task = await service.update_task(task_id, task_data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.delete("/{task_id}", response_model=Dict)
async def delete_task(
    task_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """删除任务"""
    service = TaskService(db)
    success = await service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # 删除相关的结果
    scraper_service = ScraperService()
    await scraper_service.delete_results(task_id)
    
    return {"message": "Task and related results deleted successfully"}

@router.post("/{task_id}/start", response_model=TaskStatusResponse)
async def start_task(
    task_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """启动任务"""
    service = TaskService(db)
    task = await service.start_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatusResponse(
        id=task.id,
        status=task.status,
        progress=task.progress,
        result_count=task.result_count,
        started_at=task.started_at,
        completed_at=task.completed_at
    )

@router.post("/{task_id}/stop", response_model=TaskStatusResponse)
async def stop_task(
    task_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """停止任务"""
    service = TaskService(db)
    task = await service.stop_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatusResponse(
        id=task.id,
        status=task.status,
        progress=task.progress,
        result_count=task.result_count,
        started_at=task.started_at,
        completed_at=task.completed_at
    )

@router.get("/{task_id}/results", response_model=ResultsResponse)
async def get_task_results(
    task_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    data_type: Optional[str] = None
):
    """获取任务结果"""
    scraper_service = ScraperService()
    results = await scraper_service.get_results(
        task_id=task_id,
        data_type=data_type,
        skip=skip,
        limit=limit
    )
    
    return ResultsResponse(
        total=results["total"],
        data=results["data"]
    )

@router.post("/batch", response_model=List[TaskResponse])
async def create_batch_tasks(
    tasks: List[TaskCreate],
    db: AsyncSession = Depends(get_db)
):
    """批量创建采集任务"""
    service = TaskService(db)
    results = []
    for task_data in tasks:
        task = await service.create_task(task_data)
        results.append(task)
    return results

@router.get("/search/results", response_model=ResultsResponse)
async def search_results(
    query: str = Query(..., description="搜索查询字符串"),
    data_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """搜索采集结果"""
    scraper_service = ScraperService()
    
    # 解析查询字符串为查询字典
    query_dict = {}
    for item in query.split(","):
        if ":" in item:
            key, value = item.split(":", 1)
            query_dict[key.strip()] = value.strip()
    
    results = await scraper_service.get_results(
        data_type=data_type,
        query=query_dict,
        skip=skip,
        limit=limit
    )
    
    return ResultsResponse(
        total=results["total"],
        data=results["data"]
    )

@router.post("/export/{task_id}")
async def export_task_results(
    task_id: str,
    format: str = Query("json", regex="^(json|csv)$")
):
    """导出任务结果"""
    from fastapi.responses import JSONResponse, StreamingResponse
    import csv
    import io
    
    scraper_service = ScraperService()
    results = await scraper_service.get_results(task_id=task_id, limit=10000)
    
    if format == "json":
        return JSONResponse(content=results)
    else:  # csv
        # 创建CSV输出
        output = io.StringIO()
        if not results["data"]:
            writer = csv.writer(output)
            writer.writerow(["No data available"])
        else:
            # 获取第一条数据的所有字段作为标题
            first_item = results["data"][0]
            flat_data = {}
            
            # 扁平化嵌套数据
            def flatten_dict(d, prefix=""):
                for k, v in d.items():
                    if isinstance(v, dict):
                        flatten_dict(v, f"{prefix}{k}.")
                    else:
                        flat_data[f"{prefix}{k}"] = v
            
            flatten_dict(first_item)
            fieldnames = flat_data.keys()
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            # 写入所有数据
            for item in results["data"]:
                flat_item = {}
                flatten_dict(item)
                writer.writerow(flat_item)
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=task_{task_id}_results.csv"}
        )