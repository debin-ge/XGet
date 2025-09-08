from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from app.core.data_connector import data_connector
from app.core.cache import cache_response
from app.core.config import settings
from app.core.logging import logger


class TaskAnalysisService:
    """任务分析服务"""
    
    @cache_response(expire=settings.CACHE_TTL, key_prefix="analytics:tasks:realtime")
    async def get_realtime_analytics(self) -> Dict[str, Any]:
        """获取任务实时统计数据"""
        try:
            # 从scraper_db获取实时数据
            task_stats_query = """
                SELECT 
                    COUNT(*) as total_tasks,
                    COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed_tasks,
                    COUNT(CASE WHEN status = 'FAILED' THEN 1 END) as failed_tasks,
                    AVG(duration) as avg_duration
                FROM task_executions
            """
            
            # 执行查询
            task_stats = await data_connector.query_external_db("scraper_db", task_stats_query)

            logger.info(f"task stats: {task_stats}")
            
            # 计算指标
            task_data = task_stats[0] if task_stats else {}
            
            total_tasks = task_data.get('total_tasks', 0)
            completed_tasks = task_data.get('completed_tasks', 0)
            failed_tasks = task_data.get('failed_tasks', 0)
            
            if total_tasks > 0:
                success_rate = (completed_tasks / total_tasks) * 100
            else:
                success_rate = 0.0
            
            # 处理可能的None值
            avg_duration = task_data.get('avg_duration')
            
            return {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "success_rate": round(success_rate, 2) if success_rate is not None else 0.0,
                "avg_duration": round(avg_duration, 2) if avg_duration is not None else 0.0,
            }
            
        except Exception as e:
            print(f"Task realtime analytics error: {e}")
            return {
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "last_updated": datetime.now().isoformat(),
                "error": str(e)
            }
    
    @cache_response(expire=settings.CACHE_TTL, key_prefix="analytics:tasks:history")
    async def get_history_analytics(self, time_range: str = "24h", 
                                  task_type: Optional[str] = None, 
                                  status: Optional[str] = None) -> Dict[str, Any]:
        """获取任务历史统计数据"""
        try:
            # 根据时间范围确定时间间隔
            if time_range == "1h":
                interval = "1 hour"
                time_format = "HH24:MI"
            elif time_range == "24h":
                interval = "24 hours"
                time_format = "HH24:MI"
            elif time_range == "7d":
                interval = "7 days"
                time_format = "YYYY-MM-DD"
            elif time_range == "30d":
                interval = "30 days"
                time_format = "YYYY-MM-DD"
            else:
                interval = "24 hours"
                time_format = "HH24:MI"
            
            # 构建基础查询条件
            base_conditions = ["te.started_at >= NOW() - INTERVAL '{interval}'".format(interval=interval)]
            if task_type:
                base_conditions.append(f"t.task_type = '{task_type}'")
            if status:
                base_conditions.append(f"te.status = '{status}'")
            
            where_clause = " AND ".join(base_conditions)
            
            # 执行效率趋势查询
            trend_query = f"""
                SELECT 
                    DATE_TRUNC('hour', te.started_at) as time_bucket,
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN te.status = 'COMPLETED' THEN 1 ELSE 0 END) as successful_executions,
                    AVG(te.duration) as avg_duration,
                    AVG(t.result_count) as avg_results
                FROM task_executions te
                JOIN tasks t ON te.task_id = t.id
                WHERE {where_clause}
                GROUP BY time_bucket
                ORDER BY time_bucket
            """
            
            # 错误分析查询
            error_query = f"""
                SELECT 
                    te.error_message,
                    COUNT(*) as error_count
                FROM task_executions te
                WHERE te.started_at >= NOW() - INTERVAL '{interval}'
                AND te.status = 'FAILED'
                AND te.error_message IS NOT NULL
                GROUP BY te.error_message
                ORDER BY error_count DESC
                LIMIT 10
            """
            
            # 任务类型分布查询
            type_query = f"""
                SELECT 
                    t.task_type,
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN te.status = 'COMPLETED' THEN 1 ELSE 0 END) as successful_executions,
                    AVG(te.duration) as avg_duration
                FROM task_executions te
                JOIN tasks t ON te.task_id = t.id
                WHERE te.started_at >= NOW() - INTERVAL '{interval}'
                GROUP BY t.task_type
                ORDER BY total_executions DESC
            """
            
            # 执行查询
            trend_data = await data_connector.query_external_db("scraper_db", trend_query)
            error_data = await data_connector.query_external_db("scraper_db", error_query)
            type_data = await data_connector.query_external_db("scraper_db", type_query)
            
            # 处理趋势数据
            trends = []
            for row in trend_data:
                success_rate = (row['successful_executions'] / row['total_executions'] * 100) if row['total_executions'] > 0 else 0
                trends.append({
                    "timestamp": row['time_bucket'].isoformat(),
                    "total_executions": row['total_executions'],
                    "successful_executions": row['successful_executions'],
                    "success_rate": round(success_rate, 2),
                    "avg_duration": round(row['avg_duration'], 2) if row['avg_duration'] is not None else 0.0,
                    "avg_results": round(row['avg_results'], 2) if row['avg_results'] is not None else 0.0
                })
            
            # 处理错误数据
            error_analysis = []
            for row in error_data:
                error_analysis.append({
                    "error_message": row['error_message'],
                    "count": row['error_count']
                })
            
            # 处理任务类型数据
            type_distribution = []
            for row in type_data:
                success_rate = (row['successful_executions'] / row['total_executions'] * 100) if row['total_executions'] > 0 else 0
                type_distribution.append({
                    "task_type": row['task_type'],
                    "total_executions": row['total_executions'],
                    "success_rate": round(success_rate, 2),
                    "avg_duration": round(row['avg_duration'], 2) if row['avg_duration'] is not None else 0.0
                })
            
            return {
                "time_range": time_range,
                "task_type_filter": task_type,
                "status_filter": status,
                "efficiency_trends": trends,
                "error_analysis": error_analysis,
                "type_distribution": type_distribution
            }
            
        except Exception as e:
            print(f"Task history analytics error: {e}")
            return {
                "time_range": time_range,
                "task_type_filter": task_type,
                "status_filter": status,
                "efficiency_trends": [],
                "error_analysis": [],
                "type_distribution": [],
                "error": str(e)
            }
    
    async def get_task_efficiency_stats(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """获取任务效率统计"""
        try:
            if task_id:
                # 获取特定任务的详细统计
                task_query = f"""
                    SELECT 
                        t.*,
                        COUNT(te.id) as total_executions,
                        SUM(CASE WHEN te.status = 'COMPLETED' THEN 1 ELSE 0 END) as successful_executions,
                        AVG(te.duration) as avg_duration,
                        AVG(t.result_count) as avg_results
                    FROM tasks t
                    LEFT JOIN task_executions te ON t.id = te.task_id
                    WHERE t.id = '{task_id}'
                    GROUP BY t.id
                """
                
                execution_query = f"""
                    SELECT 
                        status,
                        COUNT(*) as count,
                        AVG(duration) as avg_duration
                    FROM task_executions 
                    WHERE task_id = '{task_id}'
                    GROUP BY status
                """
                
                task_info = await data_connector.query_external_db("scraper_db", task_query)
                execution_stats = await data_connector.query_external_db("scraper_db", execution_query)
                
                if not task_info:
                    return {"error": "Task not found"}
                
                return {
                    "task_info": task_info[0],
                    "execution_stats": execution_stats
                }
            else:
                # 获取所有任务的汇总统计
                summary_query = """
                    SELECT 
                        COUNT(*) as total_tasks,
                        COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed_tasks,
                        COUNT(CASE WHEN status = 'FAILED' THEN 1 END) as failed_tasks,
                        AVG(result_count) as avg_results_per_task,
                        COUNT(DISTINCT task_type) as unique_task_types
                    FROM tasks
                    WHERE created_at >= NOW() - INTERVAL '7 days'
                """
                
                efficiency_query = """
                    SELECT 
                        AVG(te.duration) as avg_execution_time,
                        AVG(t.result_count) as avg_results,
                        COUNT(DISTINCT te.account_id) as unique_accounts_used,
                        COUNT(DISTINCT te.proxy_id) as unique_proxies_used
                    FROM task_executions te
                    JOIN tasks t ON te.task_id = t.id
                    WHERE te.started_at >= NOW() - INTERVAL '24 hours'
                """
                
                summary = await data_connector.query_external_db("scraper_db", summary_query)
                efficiency = await data_connector.query_external_db("scraper_db", efficiency_query)
                
                return {
                    "summary": summary[0] if summary else {},
                    "efficiency_metrics": efficiency[0] if efficiency else {}
                }
                
        except Exception as e:
            print(f"Task efficiency stats error: {e}")
            return {"error": str(e)}

    @cache_response(expire=settings.CACHE_TTL, key_prefix="analytics:tasks:trends")
    async def get_task_trends(self, time_range: str = "7d", 
                            task_type: Optional[str] = None, 
                            status: Optional[str] = None) -> Dict[str, Any]:
        """获取任务趋势统计数据"""
        try:
            # 根据时间范围确定时间间隔和分组粒度
            if time_range == "1h":
                interval = "1 hour"
                time_group = "MINUTE"
                time_format = "HH24:MI"
            elif time_range == "24h":
                interval = "24 hours"
                time_group = "HOUR"
                time_format = "HH24:00"
            elif time_range == "7d":
                interval = "7 days"
                time_group = "DAY"
                time_format = "YYYY-MM-DD"
            elif time_range == "30d":
                interval = "30 days"
                time_group = "DAY"
                time_format = "YYYY-MM-DD"
            else:
                interval = "7 days"
                time_group = "DAY"
                time_format = "YYYY-MM-DD"
            
            # 构建基础查询条件
            base_conditions = [f"te.started_at >= NOW() - INTERVAL '{interval}'"]
            if task_type:
                base_conditions.append(f"t.task_type = '{task_type}'")
            if status:
                base_conditions.append(f"te.status = '{status}'")
            
            where_clause = " AND ".join(base_conditions)
            
            # 任务趋势查询 - 按时间分组统计
            trends_query = f"""
                SELECT 
                    DATE_TRUNC('{time_group}', te.started_at) as time_bucket,
                    COUNT(*) as total_tasks,
                    COUNT(CASE WHEN te.status = 'COMPLETED' THEN 1 END) as completed_tasks,
                    COUNT(CASE WHEN te.status = 'FAILED' THEN 1 END) as failed_tasks,
                    COUNT(CASE WHEN te.status = 'PENDING' THEN 1 END) as pending_tasks,
                    COUNT(CASE WHEN te.status = 'RUNNING' THEN 1 END) as running_tasks
                FROM task_executions te
                JOIN tasks t ON te.task_id = t.id
                WHERE {where_clause}
                GROUP BY time_bucket
                ORDER BY time_bucket
            """
            
            # 执行查询
            trends_data = await data_connector.query_external_db("scraper_db", trends_query)
            
            # 处理趋势数据，格式化为ECharts需要的格式
            time_series = []
            completed_series = []
            failed_series = []
            pending_series = []
            running_series = []
            total_series = []
            success_rate_series = []
            
            for row in trends_data:
                timestamp = row['time_bucket']
                total = row['total_tasks']
                completed = row['completed_tasks']
                failed = row['failed_tasks']
                pending = row['pending_tasks']
                running = row['running_tasks']
                
                # 计算成功率
                success_rate = (completed / total * 100) if total > 0 else 0
                
                # 格式化时间戳
                if time_group == "MINUTE":
                    time_label = timestamp.strftime("%H:%M")
                elif time_group == "HOUR":
                    time_label = timestamp.strftime("%H:00")
                else:
                    time_label = timestamp.strftime("%Y-%m-%d")
                
                time_series.append(time_label)
                completed_series.append(completed)
                failed_series.append(failed)
                pending_series.append(pending)
                running_series.append(running)
                total_series.append(total)
                success_rate_series.append(round(success_rate, 2))
            
            return {
                "time_range": time_range,
                "time_group": time_group,
                "task_type_filter": task_type,
                "status_filter": status,
                "time_labels": time_series,
                "series_data": {
                    "completed_tasks": completed_series,
                    "failed_tasks": failed_series,
                    "pending_tasks": pending_series,
                    "running_tasks": running_series,
                    "total_tasks": total_series,
                    "success_rate": success_rate_series
                },
                "summary": {
                    "total_period_tasks": sum(total_series),
                    "total_completed": sum(completed_series),
                    "total_failed": sum(failed_series),
                    "overall_success_rate": round((sum(completed_series) / sum(total_series) * 100), 2) if sum(total_series) > 0 else 0,
                }
            }
            
        except Exception as e:
            print(f"Task trends analytics error: {e}")
            return {
                "time_range": time_range,
                "task_type_filter": task_type,
                "status_filter": status,
                "time_labels": [],
                "series_data": {
                    "completed_tasks": [],
                    "failed_tasks": [],
                    "pending_tasks": [],
                    "running_tasks": [],
                    "total_tasks": [],
                    "success_rate": []
                },
                "summary": {
                    "total_period_tasks": 0,
                    "total_completed": 0,
                    "total_failed": 0,
                    "overall_success_rate": 0,
                },
                "error": str(e)
            }


# 全局任务分析服务实例
task_analysis_service = TaskAnalysisService()