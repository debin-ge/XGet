from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from ..db.database import get_db
from ..schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskStatusResponse, TaskListResponse
from ..schemas.result import ResultsResponse
from ..services.task_service import TaskService
from ..services.scraper_service import ScraperService
from ..services.task_execution_service import TaskExecutionService
from ..schemas.task_execution import TaskExecutionCreate, TaskExecutionUpdate
from ..core.auth import get_current_user_id
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate, 
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """创建采集任务"""
    service = TaskService(db)
    # 自动设置用户ID
    task.user_id = current_user_id
    return await service.create_task(task)

@router.get("/", response_model=TaskListResponse)
async def get_tasks(
    page: int = Query(1, ge=1, description="页码"), 
    size: int = Query(20, ge=1, le=100, description="每页数量"), 
    status: Optional[str] = Query(None, description="任务状态筛选"),
    task_type: Optional[str] = Query(None, description="任务类型筛选"),
    task_name: Optional[str] = Query(None, description="按任务名称搜索"),
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """获取任务列表 - 只返回当前用户的任务"""
    service = TaskService(db)
    # 自动使用当前用户ID进行筛选，确保用户只能看到自己的任务
    return await service.get_tasks_paginated(page, size, status, task_type,task_name, current_user_id)

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str, 
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """获取任务详情"""
    service = TaskService(db)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 检查用户权限：只能访问自己的任务
    if task.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied: You can only access your own tasks")
    
    return task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str, 
    task_data: TaskUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """更新任务信息"""
    service = TaskService(db)
    
    # 先检查任务是否存在且属于当前用户
    existing_task = await service.get_task(task_id)
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if existing_task.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied: You can only update your own tasks")
    
    task = await service.update_task(task_id, task_data)
    return task

@router.delete("/{task_id}", response_model=Dict)
async def delete_task(
    task_id: str, 
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """删除任务"""
    service = TaskService(db)
    
    # 先检查任务是否存在且属于当前用户
    existing_task = await service.get_task(task_id)
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if existing_task.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied: You can only delete your own tasks")
    
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
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """启动任务"""
    service = TaskService(db)
    
    # 先检查任务是否存在且属于当前用户
    existing_task = await service.get_task(task_id)
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if existing_task.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied: You can only start your own tasks")
    
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
        task_name=task.task_name,
        status=task.status,
        error_message=task.error_message,
        created_at=task.created_at,
        updated_at=task.updated_at
    )

@router.post("/{task_id}/stop", response_model=TaskStatusResponse)
async def stop_task(
    task_id: str, 
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """停止任务"""
    service = TaskService(db)
    
    # 先检查任务是否存在且属于当前用户
    existing_task = await service.get_task(task_id)
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if existing_task.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied: You can only stop your own tasks")
    
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
        task_name=task.task_name,
        status=task.status,
        error_message=task.error_message,
        created_at=task.created_at,
        updated_at=task.updated_at
    )

@router.get("/{task_id}/results", response_model=ResultsResponse)
async def get_task_results(
    task_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    data_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """获取任务结果"""
    # 先检查任务是否存在且属于当前用户
    task_service = TaskService(db)
    existing_task = await task_service.get_task(task_id)
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if existing_task.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied: You can only access results of your own tasks")
    
    scraper_service = ScraperService()
    results = await scraper_service.get_results(
        task_id=task_id,
        data_type=data_type,
        skip=skip,
        limit=limit
    )
    
    # 计算页码
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return ResultsResponse.create(
        items=results["data"],
        total=results["total"],
        page=page,
        size=limit
    )

@router.post("/batch", response_model=List[TaskResponse])
async def create_batch_tasks(
    tasks: List[TaskCreate],
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """批量创建采集任务"""
    service = TaskService(db)
    results = []
    for task_data in tasks:
        # 自动设置用户ID
        task_data.user_id = current_user_id
        task = await service.create_task(task_data)
        results.append(task)
    return results

@router.get("/search/results", response_model=ResultsResponse)
async def search_results(
    query: str = Query(..., description="搜索查询字符串"),
    data_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """搜索采集结果 - 只搜索当前用户的任务结果"""
    # 先获取当前用户的所有任务ID
    task_service = TaskService(db)
    user_tasks = await task_service.get_tasks_paginated(1, 1000, None, None,None, current_user_id)
    user_task_ids = [task.id for task in user_tasks.items]
    
    if not user_task_ids:
        # 如果用户没有任务，返回空结果
        return ResultsResponse.create(
            items=[],
            total=0,
            page=1,
            size=limit
        )
    
    scraper_service = ScraperService()
    
    # 解析查询字符串为查询字典
    query_dict = {}
    for item in query.split(","):
        if ":" in item:
            key, value = item.split(":", 1)
            query_dict[key.strip()] = value.strip()
    
    # 添加任务ID限制
    query_dict["task_id"] = {"$in": user_task_ids}
    
    results = await scraper_service.get_results(
        data_type=data_type,
        query=query_dict,
        skip=skip,
        limit=limit
    )
    
    # 计算页码
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return ResultsResponse.create(
        items=results["data"],
        total=results["total"],
        page=page,
        size=limit
    )

