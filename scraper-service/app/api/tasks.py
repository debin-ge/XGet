from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from ..db.database import get_db
from ..schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskStatusResponse
from ..schemas.result import ResultsResponse
from ..services.task_service import TaskService
from ..services.scraper_service import ScraperService
from ..services.task_execution_service import TaskExecutionService
from ..schemas.task_execution import TaskExecutionCreate, TaskExecutionUpdate
from datetime import datetime

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
    
    # 创建任务执行记录
    execution_service = TaskExecutionService(db)
    await execution_service.create_execution(
        TaskExecutionCreate(
            task_id=task_id,
            account_id=task.account_id,
            proxy_id=task.proxy_id,
            status="RUNNING",
            started_at=datetime.now()
        )
    )
    
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
    
    # 更新最新的任务执行记录
    execution_service = TaskExecutionService(db)
    executions = await execution_service.get_executions_by_task(task_id)
    if executions:
        latest_execution = executions[0]  # 最新的执行记录
        await execution_service.update_execution(
            latest_execution.id,
            TaskExecutionUpdate(
                status="STOPPED",
                completed_at=datetime.now()
            )
        )
    
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