import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import func, text, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.proxy import Proxy, ProxyQuality, ProxyUsageHistory
from app.schemas.analytics import (
    AnalyticsResponse,
    ProxyStatus,
    UsageStatus,
    RealtimeProxyAnalytics,
    ProxyTrendData,
    GeographicDistribution,
    ISPDistribution,
    HistoryProxyAnalytics,
    ProxyQualityStats,
    ProxyQualitySummary,
    ProxyQualityDistribution,
    RecentProxyActivity
)
from app.core.redis import RedisManager
from app.core.cache import _serialize_object

logger = logging.getLogger(__name__)


class ProxyAnalyticsService:
    """代理分析服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache_ttl = 300  # 5分钟缓存
    
    def _get_cache_key(self, prefix: str, *args) -> str:
        """生成缓存键"""
        return f"proxy_analytics:{prefix}:{':'.join(str(arg) for arg in args if arg is not None)}"
    
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
        """获取实时代理分析数据"""
        cache_key = self._get_cache_key("realtime")
        
        # 尝试从缓存获取
        cached_data = await self._get_from_cache(cache_key)
        if cached_data:
            return AnalyticsResponse(**cached_data)
        
        try:
            # 获取代理统计
            proxy_stats_query = await self.db.execute(
                text("""
                    SELECT 
                        COUNT(*) as total_proxies,
                        COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as active_proxies,
                        AVG(success_rate) as avg_success_rate,
                        AVG(latency) as avg_latency
                    FROM proxies
                    WHERE 1=1
                """)
            )
            proxy_stats = proxy_stats_query.fetchone()
            
            # 获取最近1小时的使用统计
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            usage_stats_query = await self.db.execute(
                text("""
                    SELECT 
                        COUNT(*) as total_usage,
                        SUM(CASE WHEN success = 'SUCCESS' THEN 1 ELSE 0 END) as successful_usage,
                        AVG(response_time) as avg_response_time
                    FROM proxy_usage_history 
                    WHERE created_at >= :start_time
                """),
                {"start_time": one_hour_ago}
            )
            usage_stats = usage_stats_query.fetchone()
            
            total_proxies = proxy_stats.total_proxies or 0
            active_proxies = proxy_stats.active_proxies or 0
            avg_success_rate = float(proxy_stats.avg_success_rate or 0)
            avg_latency = float(proxy_stats.avg_latency or 0)
            
            total_usage = usage_stats.total_usage or 0
            successful_usage = usage_stats.successful_usage or 0
            avg_response_time = float(usage_stats.avg_response_time or 0)
            
            # 计算最近使用的成功率
            recent_success_rate = successful_usage / total_usage if total_usage > 0 else 0.0
            
            # 构建响应数据
            realtime_data = RealtimeProxyAnalytics(
                total_proxies=total_proxies,
                active_proxies=active_proxies,
                success_rate=recent_success_rate,
                avg_latency=avg_latency,
                avg_response_time=avg_response_time,
                last_updated=datetime.utcnow()
            )
            
            response_data = {
                "success": True,
                "message": "实时代理分析数据获取成功",
                "data": realtime_data.model_dump()
            }
            
            # 缓存数据
            await self._set_cache(cache_key, response_data)
            
            return AnalyticsResponse(**response_data)
            
        except Exception as e:
            logger.error(f"获取实时代理分析数据失败: {e}")
            return AnalyticsResponse(
                success=False,
                message=f"获取实时代理分析数据失败: {str(e)}"
            )
    
    async def get_history_analytics(self, time_range: str = "24h", country: Optional[str] = None, isp: Optional[str] = None) -> AnalyticsResponse:
        """获取历史代理分析数据"""
        cache_key = self._get_cache_key("history", time_range, country, isp)
        
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
            base_conditions = ["puh.created_at >= :start_time"]
            params = {"start_time": start_time}
            
            if country:
                base_conditions.append("p.country = :country")
                params["country"] = country
            
            if isp:
                base_conditions.append("p.isp = :isp")
                params["isp"] = isp
            
            where_clause = " AND ".join(base_conditions) if base_conditions else "1=1"
            
            # 获取趋势数据
            trends_query = await self.db.execute(
                text(f"""
                    SELECT 
                        DATE_TRUNC('hour', puh.created_at) as time_bucket,
                        COUNT(*) as total_requests,
                        SUM(CASE WHEN puh.success = 'SUCCESS' THEN 1 ELSE 0 END) as successful_requests,
                        AVG(puh.response_time) as avg_response_time,
                        AVG(puh.latency) as avg_latency
                    FROM proxy_usage_history puh
                    JOIN proxies p ON puh.proxy_id = p.id
                    WHERE {where_clause}
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                """),
                params
            )
            trends_data = trends_query.fetchall()
            
            # 构建趋势数据
            trends = []
            for row in trends_data:
                total_requests = row.total_requests or 0
                successful_requests = row.successful_requests or 0
                failed_requests = total_requests - successful_requests
                success_rate = successful_requests / total_requests if total_requests > 0 else 0.0
                
                trend_item = ProxyTrendData(
                    time_bucket=row.time_bucket,
                    total_requests=total_requests,
                    successful_requests=successful_requests,
                    failed_requests=failed_requests,
                    success_rate=success_rate,
                    avg_response_time=float(row.avg_response_time or 0),
                    avg_latency=float(row.avg_latency or 0)
                )
                trends.append(trend_item.model_dump())
            
            # 获取地理分布
            geo_query = await self.db.execute(
                text(f"""
                    SELECT 
                        p.country,
                        COUNT(DISTINCT p.id) as total_proxies,
                        COUNT(DISTINCT CASE WHEN p.status = 'ACTIVE' THEN p.id END) as active_proxies,
                        AVG(p.success_rate) as avg_success_rate,
                        AVG(p.latency) as avg_latency,
                        COUNT(puh.id) as total_usage,
                        SUM(CASE WHEN puh.success = 'SUCCESS' THEN 1 ELSE 0 END) as successful_usage
                    FROM proxies p
                    LEFT JOIN proxy_usage_history puh ON p.id = puh.proxy_id 
                        AND puh.created_at >= :start_time
                    WHERE 1=1
                    {"AND p.country = :country" if country else ""}
                    {"AND p.isp = :isp" if isp else ""}
                    GROUP BY p.country
                    ORDER BY total_proxies DESC
                """),
                params
            )
            geo_data = geo_query.fetchall()
            
            geographic_distribution = []
            for row in geo_data:
                total_usage = row.total_usage or 0
                successful_usage = row.successful_usage or 0
                avg_success_rate = float(row.avg_success_rate or 0)
                avg_response_time = float(row.avg_latency or 0)  # 使用latency作为响应时间近似
                avg_latency = float(row.avg_latency or 0)
                
                geo_item = GeographicDistribution(
                    country=row.country,
                    total_proxies=row.total_proxies or 0,
                    active_proxies=row.active_proxies or 0,
                    avg_success_rate=avg_success_rate,
                    avg_response_time=avg_response_time,
                    avg_latency=avg_latency,
                    total_usage=total_usage,
                    successful_usage=successful_usage
                )
                geographic_distribution.append(geo_item.model_dump())
            
            # 获取ISP分布
            isp_query = await self.db.execute(
                text(f"""
                    SELECT 
                        p.isp,
                        COUNT(DISTINCT p.id) as total_proxies,
                        COUNT(DISTINCT CASE WHEN p.status = 'ACTIVE' THEN p.id END) as active_proxies,
                        AVG(p.success_rate) as avg_success_rate,
                        AVG(p.latency) as avg_latency,
                        COUNT(puh.id) as total_usage,
                        SUM(CASE WHEN puh.success = 'SUCCESS' THEN 1 ELSE 0 END) as successful_usage
                    FROM proxies p
                    LEFT JOIN proxy_usage_history puh ON p.id = puh.proxy_id 
                        AND puh.created_at >= :start_time
                    WHERE p.isp IS NOT NULL
                    {"AND p.country = :country" if country else ""}
                    {"AND p.isp = :isp" if isp else ""}
                    GROUP BY p.isp
                    ORDER BY total_proxies DESC
                """),
                params
            )
            isp_data = isp_query.fetchall()
            
            isp_distribution = []
            for row in isp_data:
                total_usage = row.total_usage or 0
                successful_usage = row.successful_usage or 0
                avg_success_rate = float(row.avg_success_rate or 0)
                avg_response_time = float(row.avg_latency or 0)  # 使用latency作为响应时间近似
                avg_latency = float(row.avg_latency or 0)
                
                isp_item = ISPDistribution(
                    isp=row.isp,
                    total_proxies=row.total_proxies or 0,
                    active_proxies=row.active_proxies or 0,
                    avg_success_rate=avg_success_rate,
                    avg_response_time=avg_response_time,
                    avg_latency=avg_latency,
                    total_usage=total_usage,
                    successful_usage=successful_usage
                )
                isp_distribution.append(isp_item.model_dump())
            
            history_data = HistoryProxyAnalytics(
                time_range=time_range,
                trends=trends,
                geographic_distribution=geographic_distribution,
                isp_distribution=isp_distribution
            )
            
            response_data = {
                "success": True,
                "message": "历史代理分析数据获取成功",
                "data": history_data.model_dump()
            }
            
            # 缓存数据
            await self._set_cache(cache_key, response_data)
            
            return AnalyticsResponse(**response_data)
            
        except Exception as e:
            logger.error(f"获取历史代理分析数据失败: {e}")
            return AnalyticsResponse(
                success=False,
                message=f"获取历史代理分析数据失败: {str(e)}"
            )
    
    async def get_proxy_quality_stats(self, proxy_id: Optional[str] = None) -> AnalyticsResponse:
        """获取代理质量统计"""
        cache_key = self._get_cache_key("quality", proxy_id or "all")
        
        # 尝试从缓存获取
        cached_data = await self._get_from_cache(cache_key)
        if cached_data:
            return AnalyticsResponse(**cached_data)
        
        try:
            if proxy_id:
                # 获取指定代理的详细统计
                proxy_stats_query = await self.db.execute(
                    text("""
                        SELECT 
                            p.id as proxy_id,
                            p.ip,
                            p.port,
                            p.country,
                            p.city,
                            p.isp,
                            p.status,
                            p.success_rate,
                            p.latency,
                            p.last_check,
                            COALESCE(pq.total_usage, 0) as total_usage,
                            COALESCE(pq.success_count, 0) as successful_usage,
                            COALESCE(pq.quality_score, 0.8) as quality_score,
                            pq.last_used
                        FROM proxies p
                        LEFT JOIN proxy_qualities pq ON p.id = pq.proxy_id
                        WHERE p.id = :proxy_id
                    """),
                    {"proxy_id": proxy_id}
                )
                proxy_stats = proxy_stats_query.fetchone()
                
                if not proxy_stats:
                    return AnalyticsResponse(
                        success=False,
                        message="代理不存在"
                    )
                
                total_usage = proxy_stats.total_usage or 0
                successful_usage = proxy_stats.successful_usage or 0
                failed_usage = total_usage - successful_usage
                success_rate = proxy_stats.success_rate or 0.0
                avg_response_time = float(proxy_stats.latency or 0)
                quality_score = float(proxy_stats.quality_score or 0.8)
                
                quality_stats = ProxyQualityStats(
                    proxy_id=proxy_stats.proxy_id,
                    ip=proxy_stats.ip,
                    port=proxy_stats.port,
                    country=proxy_stats.country,
                    city=proxy_stats.city,
                    isp=proxy_stats.isp,
                    status=ProxyStatus(proxy_stats.status),
                    success_rate=success_rate,
                    latency=avg_response_time,
                    total_usage=total_usage,
                    successful_usage=successful_usage,
                    failed_usage=failed_usage,
                    avg_response_time=avg_response_time,
                    quality_score=quality_score,
                    last_used=proxy_stats.last_used,
                    last_check=proxy_stats.last_check
                )
                
                message = f"代理 {proxy_stats.ip}:{proxy_stats.port} 的质量统计获取成功"
                
            else:
                # 获取所有代理的汇总统计
                summary_stats_query = await self.db.execute(
                    text("""
                        SELECT 
                            COUNT(*) as total_proxies,
                            COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as active_proxies,
                            AVG(p.success_rate) as avg_success_rate,
                            AVG(p.latency) as avg_latency,
                            AVG(COALESCE(pq.quality_score, 0.8)) as avg_quality_score
                        FROM proxies p
                        LEFT JOIN proxy_qualities pq ON p.id = pq.proxy_id
                    """)
                )
                summary_data = summary_stats_query.fetchone()
                
                # 获取质量分布
                quality_dist_query = await self.db.execute(
                    text("""
                        SELECT 
                            CASE 
                                WHEN COALESCE(pq.quality_score, 0.8) >= 0.8 THEN 'excellent'
                                WHEN COALESCE(pq.quality_score, 0.8) >= 0.6 THEN 'good'
                                WHEN COALESCE(pq.quality_score, 0.8) >= 0.4 THEN 'fair'
                                ELSE 'poor'
                            END as quality_category,
                            COUNT(*) as count
                        FROM proxies p
                        LEFT JOIN proxy_qualities pq ON p.id = pq.proxy_id
                        GROUP BY quality_category
                        ORDER BY quality_category
                    """)
                )
                quality_dist_data = quality_dist_query.fetchall()
                
                # 构建质量分布
                quality_distribution = {}
                for row in quality_dist_data:
                    quality_distribution[row.quality_category] = row.count
                
                # 获取使用统计
                usage_stats_query = await self.db.execute(
                    text("""
                        SELECT 
                            COUNT(*) as total_usage,
                            SUM(CASE WHEN success = 'SUCCESS' THEN 1 ELSE 0 END) as successful_usage
                        FROM proxy_usage_history
                    """)
                )
                usage_stats = usage_stats_query.fetchone()
                
                total_proxies = summary_data.total_proxies or 0
                active_proxies = summary_data.active_proxies or 0
                avg_success_rate = float(summary_data.avg_success_rate or 0)
                avg_quality_score = float(summary_data.avg_quality_score or 0.8)
                avg_latency = float(summary_data.avg_latency or 0)
                avg_response_time = avg_latency  # 使用延迟作为响应时间近似
                
                total_usage = usage_stats.total_usage or 0
                successful_usage = usage_stats.successful_usage or 0
                average_success_rate = successful_usage / total_usage if total_usage > 0 else 0.0
                
                quality_summary = ProxyQualitySummary(
                    total_proxies=total_proxies,
                    active_proxies=active_proxies,
                    avg_success_rate=avg_success_rate,
                    avg_quality_score=avg_quality_score,
                    avg_latency=avg_latency,
                    avg_response_time=avg_response_time,
                    quality_distribution=quality_distribution
                )
                
                message = "代理质量汇总统计获取成功"
            
            response_data = {
                "success": True,
                "message": message,
                "data": quality_stats.model_dump() if proxy_id else quality_summary.model_dump()
            }
            
            # 缓存数据
            await self._set_cache(cache_key, response_data)
            
            return AnalyticsResponse(**response_data)
            
        except Exception as e:
            logger.error(f"获取代理质量统计失败: {e}")
            return AnalyticsResponse(
                success=False,
                message=f"获取代理质量统计失败: {str(e)}"
            )
    
    async def get_recent_proxy_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的代理相关活动"""
        try:
            # 获取最近的使用历史作为代理活动
            activities_query = await self.db.execute(
                text("""
                    SELECT 
                        puh.id,
                        puh.proxy_id,
                        puh.proxy_ip,
                        puh.proxy_port,
                        puh.created_at as timestamp,
                        puh.success as status,
                        puh.response_time,
                        puh.latency,
                        puh.account_id,
                        puh.task_id,
                        puh.service_name
                    FROM proxy_usage_history puh
                    JOIN proxies p ON puh.proxy_id = p.id
                    ORDER BY puh.created_at DESC
                    LIMIT :limit
                """),
                {"limit": limit}
            )
            activities_data = activities_query.fetchall()
            
            activities = []
            for row in activities_data:
                # 构建活动描述
                if row.status == 'SUCCESS':
                    description = f"代理 {row.proxy_ip}:{row.proxy_port} 使用成功"
                    success = True
                else:
                    description = f"代理 {row.proxy_ip}:{row.proxy_port} 使用失败"
                    success = False
                
                # 构建详情
                details = {
                    "proxy_id": row.proxy_id,
                    "proxy_ip": row.proxy_ip,
                    "proxy_port": row.proxy_port,
                    "response_time": row.response_time,
                    "latency": row.latency,
                    "account_id": row.account_id,
                    "task_id": row.task_id,
                    "service_name": row.service_name
                }
                
                activity = RecentProxyActivity(
                    id=str(row.id),
                    proxy_id=row.proxy_id,
                    proxy_ip=row.proxy_ip,
                    proxy_port=row.proxy_port,
                    timestamp=row.timestamp,
                    status=UsageStatus(row.status),
                    response_time=row.response_time,
                    latency=row.latency,
                    account_id=row.account_id,
                    task_id=row.task_id,
                    service_name=row.service_name,
                    success=success,
                    description=description
                )
                activities.append(activity.model_dump())
            
            return activities
            
        except Exception as e:
            logger.error(f"获取最近代理活动失败: {e}")
            return []
    
    async def invalidate_proxy_analytics_cache(self):
        """清除代理分析缓存"""
        try:
            # 获取所有proxy_analytics相关的键
            pattern = "proxy_analytics:*"
            deleted_count = await RedisManager.delete_keys(pattern)
            logger.info(f"清除了 {deleted_count} 个代理分析缓存键")
            
        except Exception as e:
            logger.error(f"清除代理分析缓存失败: {e}")