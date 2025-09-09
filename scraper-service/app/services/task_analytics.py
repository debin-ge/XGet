import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import func, text, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.task import Task
from app.models.task_execution import TaskExecution
from app.schemas.analytics import (
    AnalyticsResponse,
    TaskStatus,
    ExecutionStatus,
    TimeGranularity,
    RealtimeTaskAnalytics,
    TaskEfficiencyTrend,
    TaskErrorAnalysis,
    TaskTypeDistribution,
    HistoryTaskAnalytics,
    TaskExecutionStats,
    TaskEfficiencySummary,
    TaskTrendSeries,
    TaskTrendData,
    RecentTaskActivity
)
from app.core.redis import RedisManager
from app.core.cache import _serialize_object

logger = logging.getLogger(__name__)


class TaskAnalyticsService:
    """任务分析服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache_ttl = 300  # 5分钟缓存
    
    def _get_cache_key(self, prefix: str, *args) -> str:
        """生成缓存键"""
        return f"task_analytics:{prefix}:{':'.join(str(arg) for arg in args if arg is not None)}"
    
    async def _get_from_cache(self, key: str) -> Optional[Dict]:
        """从缓存获取数据"""
        try:
            return await RedisManager.get_json(key)
        except Exception as e:
            logger.warning(f"缓存读取失败 {key}: {e}")
            return None
    
    async def _set_cache(self, key: str, data: Dict, ttl: Optional[int] = None):
        """设置缓存数据"""
        try:
            ttl = ttl or self.cache_ttl
            # 序列化数据以处理datetime对象
            serialized_data = _serialize_object(data)
            await RedisManager.set_json(key, serialized_data, ttl)
        except Exception as e:
            logger.warning(f"缓存设置失败 {key}: {e}")
    
    async def get_realtime_analytics(self) -> AnalyticsResponse:
        """获取实时任务分析数据"""
        cache_key = self._get_cache_key("realtime")
        
        # 尝试从缓存获取
        cached_data = await self._get_from_cache(cache_key)
        if cached_data:
            return AnalyticsResponse(**cached_data)
        
        try:
            # 获取任务执行统计
            task_stats_query = await self.db.execute(
                text("""
                    SELECT 
                        COUNT(*) as total_tasks,
                        COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed_tasks,
                        COUNT(CASE WHEN status = 'FAILED' THEN 1 END) as failed_tasks,
                        AVG(duration) as avg_duration
                    FROM task_executions
                """)
            )
            task_stats = task_stats_query.fetchone()
            
            total_tasks = task_stats.total_tasks or 0
            completed_tasks = task_stats.completed_tasks or 0
            failed_tasks = task_stats.failed_tasks or 0
            avg_duration = float(task_stats.avg_duration or 0)
            
            # 计算成功率
            success_rate = completed_tasks / total_tasks if total_tasks > 0 else 0.0
            
            # 构建响应数据
            realtime_data = RealtimeTaskAnalytics(
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks,
                success_rate=success_rate,
                avg_duration=avg_duration,
                last_updated=datetime.utcnow()
            )
            
            response_data = {
                "success": True,
                "message": "实时任务分析数据获取成功",
                "data": realtime_data.model_dump()
            }
            
            # 缓存数据
            await self._set_cache(cache_key, response_data)
            
            return AnalyticsResponse(**response_data)
            
        except Exception as e:
            logger.error(f"获取实时任务分析数据失败: {e}")
            return AnalyticsResponse(
                success=False,
                message=f"获取实时任务分析数据失败: {str(e)}"
            )
    
    async def get_history_analytics(self, time_range: str = "24h", task_type: Optional[str] = None, status: Optional[str] = None) -> AnalyticsResponse:
        """获取历史任务分析数据"""
        cache_key = self._get_cache_key("history", time_range, task_type, status)
        
        # 尝试从缓存获取
        cached_data = await self._get_from_cache(cache_key)
        if cached_data:
            return AnalyticsResponse(**cached_data)
        
        try:
            # 解析时间范围
            time_ranges = {
                "1h": timedelta(hours=1),
                "24h": timedelta(hours=24),
                "7d": timedelta(days=7),
                "30d": timedelta(days=30)
            }
            
            if time_range not in time_ranges:
                time_range = "24h"
            
            interval = time_ranges[time_range]
            start_time = datetime.utcnow() - interval
            
            # 构建基础查询条件
            base_conditions = ["te.started_at >= :start_time"]
            params = {"start_time": start_time}
            
            if task_type:
                base_conditions.append("t.task_type = :task_type")
                params["task_type"] = task_type
            
            if status:
                base_conditions.append("te.status = :status")
                params["status"] = status
            
            where_clause = " AND ".join(base_conditions) if base_conditions else "1=1"
            
            # 获取效率趋势数据
            trends_query = await self.db.execute(
                text(f"""
                    SELECT 
                        DATE_TRUNC('hour', te.started_at) as time_bucket,
                        COUNT(*) as total_executions,
                        SUM(CASE WHEN te.status = 'COMPLETED' THEN 1 ELSE 0 END) as successful_executions,
                        AVG(te.duration) as avg_duration
                    FROM task_executions te
                    JOIN tasks t ON te.task_id = t.id
                    WHERE {where_clause}
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                """),
                params
            )
            trends_data = trends_query.fetchall()
            
            # 构建趋势数据
            efficiency_trends = []
            for row in trends_data:
                total_executions = row.total_executions or 0
                successful_executions = row.successful_executions or 0
                failed_executions = total_executions - successful_executions
                success_rate = successful_executions / total_executions if total_executions > 0 else 0.0
                avg_duration = float(row.avg_duration or 0)
                
                trend_item = TaskEfficiencyTrend(
                    time_bucket=row.time_bucket,
                    total_executions=total_executions,
                    successful_executions=successful_executions,
                    failed_executions=failed_executions,
                    success_rate=success_rate,
                    avg_duration=avg_duration
                )
                efficiency_trends.append(trend_item.model_dump())
            
            # 获取错误分析数据
            error_query = await self.db.execute(
                text(f"""
                    SELECT 
                        te.error_message,
                        COUNT(*) as error_count
                    FROM task_executions te
                    JOIN tasks t ON te.task_id = t.id
                    WHERE {where_clause} AND te.error_message IS NOT NULL AND te.error_message != ''
                    GROUP BY te.error_message
                    ORDER BY error_count DESC
                    LIMIT 10
                """),
                params
            )
            error_data = error_query.fetchall()
            
            # 计算总错误数
            total_errors_query = await self.db.execute(
                text(f"""
                    SELECT COUNT(*) as total
                    FROM task_executions te
                    JOIN tasks t ON te.task_id = t.id
                    WHERE {where_clause} AND te.error_message IS NOT NULL AND te.error_message != ''
                """),
                params
            )
            total_errors_result = total_errors_query.fetchone()
            total_errors = total_errors_result.total if total_errors_result else 0
            
            error_analysis = []
            for row in error_data:
                error_percentage = (row.error_count / total_errors * 100) if total_errors > 0 else 0.0
                
                error_item = TaskErrorAnalysis(
                    error_message=row.error_message,
                    error_count=row.error_count,
                    error_percentage=error_percentage
                )
                error_analysis.append(error_item.model_dump())
            
            # 获取类型分布数据
            type_dist_query = await self.db.execute(
                text(f"""
                    SELECT 
                        t.task_type,
                        COUNT(*) as total_executions,
                        SUM(CASE WHEN te.status = 'COMPLETED' THEN 1 ELSE 0 END) as successful_executions,
                        AVG(te.duration) as avg_duration
                    FROM task_executions te
                    JOIN tasks t ON te.task_id = t.id
                    WHERE {where_clause}
                    GROUP BY t.task_type
                    ORDER BY total_executions DESC
                """),
                params
            )
            type_dist_data = type_dist_query.fetchall()
            
            type_distribution = []
            for row in type_dist_data:
                total_executions = row.total_executions or 0
                successful_executions = row.successful_executions or 0
                failed_executions = total_executions - successful_executions
                success_rate = successful_executions / total_executions if total_executions > 0 else 0.0
                avg_duration = float(row.avg_duration or 0)
                
                type_item = TaskTypeDistribution(
                    task_type=row.task_type,
                    total_executions=total_executions,
                    successful_executions=successful_executions,
                    failed_executions=failed_executions,
                    success_rate=success_rate,
                    avg_duration=avg_duration
                )
                type_distribution.append(type_item.model_dump())
            
            history_data = HistoryTaskAnalytics(
                time_range=time_range,
                efficiency_trends=efficiency_trends,
                error_analysis=error_analysis,
                type_distribution=type_distribution
            )
            
            response_data = {
                "success": True,
                "message": "历史任务分析数据获取成功",
                "data": history_data.model_dump()
            }
            
            # 缓存数据
            await self._set_cache(cache_key, response_data)
            
            return AnalyticsResponse(**response_data)
            
        except Exception as e:
            logger.error(f"获取历史任务分析数据失败: {e}")
            return AnalyticsResponse(
                success=False,
                message=f"获取历史任务分析数据失败: {str(e)}"
            )
    
    async def get_task_efficiency_stats(self, task_id: Optional[str] = None) -> AnalyticsResponse:
        """获取任务效率统计"""
        cache_key = self._get_cache_key("efficiency", task_id or "all")
        
        # 尝试从缓存获取
        cached_data = await self._get_from_cache(cache_key)
        if cached_data:
            return AnalyticsResponse(**cached_data)
        
        try:
            if task_id:
                # 获取指定任务的详细统计
                task_stats_query = await self.db.execute(
                    text("""
                        SELECT 
                            t.id as task_id,
                            t.task_name,
                            t.task_type,
                            COUNT(*) as total_executions,
                            COUNT(CASE WHEN te.status = 'COMPLETED' THEN 1 END) as completed_executions,
                            COUNT(CASE WHEN te.status = 'FAILED' THEN 1 END) as failed_executions,
                            COUNT(CASE WHEN te.status = 'RUNNING' THEN 1 END) as running_executions,
                            AVG(te.duration) as avg_duration
                        FROM tasks t
                        JOIN task_executions te ON t.id = te.task_id
                        WHERE t.id = :task_id
                        GROUP BY t.id, t.task_name, t.task_type
                    """),
                    {"task_id": task_id}
                )
                task_stats = task_stats_query.fetchone()
                
                if not task_stats:
                    return AnalyticsResponse(
                        success=False,
                        message="任务不存在"
                    )
                
                total_executions = task_stats.total_executions or 0
                completed_executions = task_stats.completed_executions or 0
                failed_executions = task_stats.failed_executions or 0
                running_executions = task_stats.running_executions or 0
                success_rate = completed_executions / total_executions if total_executions > 0 else 0.0
                avg_duration = float(task_stats.avg_duration or 0)
                
                # 获取使用的账户和代理数
                unique_resources_query = await self.db.execute(
                    text("""
                        SELECT 
                            COUNT(DISTINCT te.account_id) as unique_accounts,
                            COUNT(DISTINCT te.proxy_id) as unique_proxies,
                            MAX(te.started_at) as last_execution
                        FROM task_executions te
                        WHERE te.task_id = :task_id
                    """),
                    {"task_id": task_id}
                )
                unique_resources = unique_resources_query.fetchone()
                
                execution_stats = TaskExecutionStats(
                    task_id=task_stats.task_id,
                    task_name=task_stats.task_name,
                    task_type=task_stats.task_type,
                    total_executions=total_executions,
                    completed_executions=completed_executions,
                    failed_executions=failed_executions,
                    running_executions=running_executions,
                    success_rate=success_rate,
                    avg_duration=avg_duration,
                    unique_accounts=unique_resources.unique_accounts or 0,
                    unique_proxies=unique_resources.unique_proxies or 0,
                    last_execution=unique_resources.last_execution
                )
                
                message = f"任务 {task_stats.task_name} 的执行统计获取成功"
                
            else:
                # 获取所有任务的汇总统计
                # 获取7天汇总
                seven_days_ago = datetime.utcnow() - timedelta(days=7)
                seven_day_summary_query = await self.db.execute(
                    text("""
                        SELECT 
                            COUNT(*) as total_executions,
                            COUNT(CASE WHEN te.status = 'COMPLETED' THEN 1 END) as completed_executions,
                            COUNT(CASE WHEN te.status = 'FAILED' THEN 1 END) as failed_executions,
                            AVG(te.duration) as avg_duration,
                            COUNT(DISTINCT te.account_id) as unique_accounts,
                            COUNT(DISTINCT te.proxy_id) as unique_proxies
                        FROM task_executions te
                        WHERE te.started_at >= :start_time
                    """),
                    {"start_time": seven_days_ago}
                )
                seven_day_summary = seven_day_summary_query.fetchone()
                
                # 获取24小时效率
                twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
                twenty_four_hour_efficiency_query = await self.db.execute(
                    text("""
                        SELECT 
                            COUNT(*) as total_executions,
                            COUNT(CASE WHEN te.status = 'COMPLETED' THEN 1 END) as completed_executions,
                            COUNT(CASE WHEN te.status = 'FAILED' THEN 1 END) as failed_executions,
                            AVG(te.duration) as avg_duration,
                            COUNT(DISTINCT te.account_id) as unique_accounts,
                            COUNT(DISTINCT te.proxy_id) as unique_proxies
                        FROM task_executions te
                        WHERE te.started_at >= :start_time
                    """),
                    {"start_time": twenty_four_hours_ago}
                )
                twenty_four_hour_efficiency = twenty_four_hour_efficiency_query.fetchone()
                
                # 构建7天汇总数据
                if seven_day_summary and seven_day_summary.total_executions > 0:
                    seven_day_data = TaskEfficiencySummary(
                        task_id=None,
                        period="7d",
                        total_executions=seven_day_summary.total_executions or 0,
                        completed_executions=seven_day_summary.completed_executions or 0,
                        failed_executions=seven_day_summary.failed_executions or 0,
                        success_rate=(seven_day_summary.completed_executions or 0) / (seven_day_summary.total_executions or 1),
                        avg_duration=float(seven_day_summary.avg_duration or 0),
                        unique_accounts=seven_day_summary.unique_accounts or 0,
                        unique_proxies=seven_day_summary.unique_proxies or 0
                    )
                else:
                    seven_day_data = None
                
                # 构建24小时效率数据
                if twenty_four_hour_efficiency and twenty_four_hour_efficiency.total_executions > 0:
                    twenty_four_hour_data = TaskEfficiencySummary(
                        task_id=None,
                        period="24h",
                        total_executions=twenty_four_hour_efficiency.total_executions or 0,
                        completed_executions=twenty_four_hour_efficiency.completed_executions or 0,
                        failed_executions=twenty_four_hour_efficiency.failed_executions or 0,
                        success_rate=(twenty_four_hour_efficiency.completed_executions or 0) / (twenty_four_hour_efficiency.total_executions or 1),
                        avg_duration=float(twenty_four_hour_efficiency.avg_duration or 0),
                        unique_accounts=twenty_four_hour_efficiency.unique_accounts or 0,
                        unique_proxies=twenty_four_hour_efficiency.unique_proxies or 0
                    )
                else:
                    twenty_four_hour_data = None
                
                efficiency_summary = {
                    "7_day_summary": seven_day_data.model_dump() if seven_day_data else None,
                    "24_hour_efficiency": twenty_four_hour_data.model_dump() if twenty_four_hour_data else None
                }
                
                message = "任务效率汇总统计获取成功"
            
            response_data = {
                "success": True,
                "message": message,
                "data": execution_stats.model_dump() if task_id else efficiency_summary
            }
            
            # 缓存数据
            await self._set_cache(cache_key, response_data)
            
            return AnalyticsResponse(**response_data)
            
        except Exception as e:
            logger.error(f"获取任务效率统计失败: {e}")
            return AnalyticsResponse(
                success=False,
                message=f"获取任务效率统计失败: {str(e)}"
            )
    
    async def get_task_trends(self, time_range: str = "24h", task_type: Optional[str] = None, status: Optional[str] = None) -> AnalyticsResponse:
        """获取任务趋势数据"""
        cache_key = self._get_cache_key("trends", time_range, task_type, status)
        
        # 尝试从缓存获取
        cached_data = await self._get_from_cache(cache_key)
        if cached_data:
            return AnalyticsResponse(**cached_data)
        
        try:
            # 解析时间范围
            time_ranges = {
                "1h": (timedelta(hours=1), TimeGranularity.MINUTE),
                "24h": (timedelta(hours=24), TimeGranularity.HOUR),
                "7d": (timedelta(days=7), TimeGranularity.HOUR),
                "30d": (timedelta(days=30), TimeGranularity.DAY)
            }
            
            if time_range not in time_ranges:
                time_range = "24h"
            
            interval, granularity = time_ranges[time_range]
            start_time = datetime.utcnow() - interval
            
            # 根据粒度确定时间截断函数
            if granularity == TimeGranularity.MINUTE:
                truncate_func = "DATE_TRUNC('minute', te.started_at)"
            elif granularity == TimeGranularity.HOUR:
                truncate_func = "DATE_TRUNC('hour', te.started_at)"
            else:  # DAY
                truncate_func = "DATE_TRUNC('day', te.started_at)"
            
            # 构建基础查询条件
            base_conditions = ["te.started_at >= :start_time"]
            params = {"start_time": start_time}
            
            if task_type:
                base_conditions.append("t.task_type = :task_type")
                params["task_type"] = task_type
            
            if status:
                base_conditions.append("te.status = :status")
                params["status"] = status
            
            where_clause = " AND ".join(base_conditions) if base_conditions else "1=1"
            
            # 获取趋势数据
            trends_query = await self.db.execute(
                text(f"""
                    SELECT 
                        {truncate_func} as time_bucket,
                        COUNT(*) as total_executions,
                        SUM(CASE WHEN te.status = 'COMPLETED' THEN 1 ELSE 0 END) as completed_executions,
                        SUM(CASE WHEN te.status = 'FAILED' THEN 1 ELSE 0 END) as failed_executions,
                        SUM(CASE WHEN te.status = 'RUNNING' THEN 1 ELSE 0 END) as running_executions
                    FROM task_executions te
                    JOIN tasks t ON te.task_id = t.id
                    WHERE {where_clause}
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                """),
                params
            )
            trends_data = trends_query.fetchall()
            
            # 构建时间标签和系列数据 - 适配前端需求
            time_labels = []
            completed_tasks = []
            failed_tasks = []
            running_tasks = []
            pending_tasks = []
            success_rate = []
            total_tasks = []
            
            for row in trends_data:
                # 格式化时间标签
                if granularity == TimeGranularity.MINUTE:
                    time_label = row.time_bucket.strftime("%H:%M")
                elif granularity == TimeGranularity.HOUR:
                    time_label = row.time_bucket.strftime("%m-%d %H:00")
                else:  # DAY
                    time_label = row.time_bucket.strftime("%m-%d")
                
                time_labels.append(time_label)
                
                total_executions = row.total_executions or 0
                completed_executions = row.completed_executions or 0
                failed_executions = row.failed_executions or 0
                running_executions = row.running_executions or 0
                pending_executions = total_executions - completed_executions - failed_executions - running_executions
                if pending_executions < 0:
                    pending_executions = 0
                success_rate_value = completed_executions / total_executions if total_executions > 0 else 0.0
                
                # 构建前端需要的数据结构
                completed_tasks.append(completed_executions)
                failed_tasks.append(failed_executions)
                running_tasks.append(running_executions)
                pending_tasks.append(pending_executions)
                success_rate.append(int(success_rate_value * 100))  # 转换为百分比
                total_tasks.append(total_executions)
            
            # 构建前端需要的数据结构
            series_data = {
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "running_tasks": running_tasks,
                "pending_tasks": pending_tasks,
                "success_rate": success_rate,
                "total_tasks": total_tasks
            }
                      
            # 计算汇总统计
            total_executions = sum(row.total_executions or 0 for row in trends_data)
            total_completed = sum(row.completed_executions or 0 for row in trends_data)
            total_failed = sum(row.failed_executions or 0 for row in trends_data)
            total_running = sum(row.running_executions or 0 for row in trends_data)
            overall_success_rate = (total_completed / total_executions * 100) if total_executions > 0 else 0
            
            summary = {
                "total_executions": total_executions,
                "total_completed": total_completed,
                "total_failed": total_failed,
                "total_running": total_running,
                "overall_success_rate": round(overall_success_rate, 2)
            }
            
            # 构建前端兼容的数据结构
            trend_data = {
                "time_labels": time_labels,
                "series_data": series_data,
                "summary": summary,
            }
            
            response_data = {
                "success": True,
                "message": "任务趋势数据获取成功",
                "data": trend_data
            }
            
            # 缓存数据
            await self._set_cache(cache_key, response_data)
            
            return AnalyticsResponse(**response_data)
            
        except Exception as e:
            logger.error(f"获取任务趋势数据失败: {e}")
            return AnalyticsResponse(
                success=False,
                message=f"获取任务趋势数据失败: {str(e)}"
            )
    
    async def get_recent_task_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的任务相关活动"""
        try:
            # 获取最近的任务执行历史作为任务活动
            activities_query = await self.db.execute(
                text("""
                    SELECT 
                        te.id,
                        te.task_id,
                        t.task_name,
                        t.task_type,
                        te.started_at as timestamp,
                        te.status,
                        te.duration,
                        te.account_id,
                        te.proxy_id,
                        te.error_message
                    FROM task_executions te
                    JOIN tasks t ON te.task_id = t.id
                    ORDER BY te.started_at DESC
                    LIMIT :limit
                """),
                {"limit": limit}
            )
            activities_data = activities_query.fetchall()
            
            activities = []
            for row in activities_data:
                # 构建活动描述
                if row.status == 'COMPLETED':
                    description = f"任务 {row.task_name} 执行成功"
                    activity_status = "success"
                    success = True
                elif row.status == 'FAILED':
                    description = f"任务 {row.task_name} 执行失败"
                    activity_status = "error"
                    success = False
                else:
                    description = f"任务 {row.task_name} 正在执行"
                    activity_status = "running"
                    success = False
                
                # 构建详情
                details = {
                    "task_id": row.task_id,
                    "task_name": row.task_name,
                    "task_type": row.task_type,
                    "execution_id": str(row.id),
                    "account_id": row.account_id,
                    "proxy_id": row.proxy_id,
                    "duration": row.duration,
                    "error_message": row.error_message
                }
                
                activity = RecentTaskActivity(
                    id=str(row.id),
                    task_id=row.task_id,
                    task_name=row.task_name,
                    task_type=row.task_type,
                    execution_id=str(row.id),
                    timestamp=row.timestamp,
                    status=activity_status,
                    description=description,
                    details=details,
                    service="scraper-service",
                    account_id=row.account_id,
                    proxy_id=row.proxy_id,
                    duration=row.duration,
                    success=success
                )
                activities.append(activity.model_dump())
            
            return activities
            
        except Exception as e:
            logger.error(f"获取最近任务活动失败: {e}")
            return []
    
    async def invalidate_task_analytics_cache(self):
        """清除任务分析缓存"""
        try:
            # 获取所有task_analytics相关的键
            pattern = "task_analytics:*"
            deleted_count = await RedisManager.delete_keys(pattern)
            logger.info(f"清除了 {deleted_count} 个任务分析缓存键")
            
        except Exception as e:
            logger.error(f"清除任务分析缓存失败: {e}")