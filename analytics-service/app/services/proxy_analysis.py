from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from app.core.data_connector import data_connector
from app.core.cache import cache_response
from app.core.config import settings


class ProxyAnalysisService:
    """代理分析服务"""
    
    @cache_response(expire=settings.CACHE_TTL, key_prefix="analytics:proxies:realtime")
    async def get_realtime_analytics(self) -> Dict[str, Any]:
        """获取代理实时统计数据"""
        try:
            # 从proxy_db获取实时数据
            proxy_stats_query = """
                SELECT 
                    COUNT(*) as total_proxies,
                    COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as active_proxies,
                    AVG(success_rate) as avg_success_rate,
                    AVG(latency) as avg_latency
                FROM proxies
            """
            
            recent_usage_query = """
                SELECT 
                    COUNT(*) as total_usage,
                    SUM(CASE WHEN success = 'SUCCESS' THEN 1 ELSE 0 END) as successful_usage,
                    AVG(response_time) as avg_response_time
                FROM proxy_usage_history 
                WHERE created_at >= NOW() - INTERVAL '1 hour'
            """
            
            # 执行查询
            proxy_stats = await data_connector.query_external_db("proxy_db", proxy_stats_query)
            usage_stats = await data_connector.query_external_db("proxy_db", recent_usage_query)
            
            # 计算指标
            proxy_data = proxy_stats[0] if proxy_stats else {}
            usage_data = usage_stats[0] if usage_stats else {}
            
            total_proxies = proxy_data.get('total_proxies', 0)
            active_proxies = proxy_data.get('active_proxies', 0)
            
            if usage_data.get('total_usage', 0) > 0:
                success_rate = (usage_data.get('successful_usage', 0) / usage_data.get('total_usage', 1)) * 100
            else:
                success_rate = proxy_data.get('avg_success_rate', 0) * 100
            
            # 处理可能的None值
            avg_latency = proxy_data.get('avg_latency')
            avg_response_time = usage_data.get('avg_response_time')
            
            return {
                "total_proxies": total_proxies,
                "active_proxies": active_proxies,
                "success_rate": round(success_rate, 2) if success_rate is not None else 0.0,
                "avg_latency": round(avg_latency, 2) if avg_latency is not None else 0.0,
                "avg_response_time": round(avg_response_time, 2) if avg_response_time is not None else 0.0,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Proxy realtime analytics error: {e}")
            return {
                "total_proxies": 0,
                "active_proxies": 0,
                "success_rate": 0.0,
                "avg_latency": 0.0,
                "avg_response_time": 0.0,
                "last_updated": datetime.now().isoformat(),
                "error": str(e)
            }
    
    @cache_response(expire=settings.CACHE_TTL, key_prefix="analytics:proxies:history")
    async def get_history_analytics(self, time_range: str = "24h", 
                                  country: Optional[str] = None, 
                                  isp: Optional[str] = None) -> Dict[str, Any]:
        """获取代理历史统计数据"""
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
            
            # 构建基础查询
            base_conditions = ["created_at >= NOW() - INTERVAL '{interval}'".format(interval=interval)]
            if country:
                base_conditions.append(f"country = '{country}'")
            if isp:
                base_conditions.append(f"isp = '{isp}'")
            
            where_clause = " AND ".join(base_conditions)
            
            # 性能趋势查询
            trend_query = f"""
                SELECT 
                    DATE_TRUNC('hour', created_at) as time_bucket,
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN success = 'SUCCESS' THEN 1 ELSE 0 END) as successful_requests,
                    AVG(response_time) as avg_response_time,
                    AVG(latency) as avg_latency
                FROM proxy_usage_history 
                WHERE {where_clause}
                GROUP BY time_bucket
                ORDER BY time_bucket
            """
            
            # 地域分布查询
            geo_query = """
                SELECT 
                    country,
                    COUNT(*) as total_usage,
                    SUM(CASE WHEN success = 'SUCCESS' THEN 1 ELSE 0 END) as successful_usage,
                    AVG(response_time) as avg_response_time,
                    AVG(latency) as avg_latency
                FROM proxy_usage_history 
                WHERE created_at >= NOW() - INTERVAL '{interval}'
                GROUP BY country
                ORDER BY total_usage DESC
            """.format(interval=interval)
            
            # ISP分布查询
            isp_query = """
                SELECT 
                    isp,
                    COUNT(*) as total_usage,
                    SUM(CASE WHEN success = 'SUCCESS' THEN 1 ELSE 0 END) as successful_usage,
                    AVG(response_time) as avg_response_time
                FROM proxy_usage_history 
                WHERE created_at >= NOW() - INTERVAL '{interval}'
                GROUP BY isp
                ORDER BY total_usage DESC
            """.format(interval=interval)
            
            # 执行查询
            trend_data = await data_connector.query_external_db("proxy_db", trend_query)
            geo_data = await data_connector.query_external_db("proxy_db", geo_query)
            isp_data = await data_connector.query_external_db("proxy_db", isp_query)
            
            # 处理趋势数据
            trends = []
            for row in trend_data:
                success_rate = (row['successful_requests'] / row['total_requests'] * 100) if row['total_requests'] > 0 else 0
                trends.append({
                    "timestamp": row['time_bucket'].isoformat(),
                    "total_requests": row['total_requests'],
                    "successful_requests": row['successful_requests'],
                    "success_rate": round(success_rate, 2),
                    "avg_response_time": round(row['avg_response_time'], 2) if row['avg_response_time'] is not None else 0.0,
                    "avg_latency": round(row['avg_latency'], 2) if row['avg_latency'] is not None else 0.0
                })
            
            # 处理地域数据
            geo_distribution = []
            for row in geo_data:
                success_rate = (row['successful_usage'] / row['total_usage'] * 100) if row['total_usage'] > 0 else 0
                geo_distribution.append({
                    "country": row['country'],
                    "total_usage": row['total_usage'],
                    "success_rate": round(success_rate, 2),
                    "avg_response_time": round(row['avg_response_time'], 2) if row['avg_response_time'] is not None else 0.0,
                    "avg_latency": round(row['avg_latency'], 2) if row['avg_latency'] is not None else 0.0
                })
            
            # 处理ISP数据
            isp_distribution = []
            for row in isp_data:
                success_rate = (row['successful_usage'] / row['total_usage'] * 100) if row['total_usage'] > 0 else 0
                isp_distribution.append({
                    "isp": row['isp'],
                    "total_usage": row['total_usage'],
                    "success_rate": round(success_rate, 2),
                    "avg_response_time": round(row['avg_response_time'], 2) if row['avg_response_time'] is not None else 0.0
                })
            
            return {
                "time_range": time_range,
                "country_filter": country,
                "isp_filter": isp,
                "performance_trends": trends,
                "geo_distribution": geo_distribution,
                "isp_distribution": isp_distribution
            }
            
        except Exception as e:
            print(f"Proxy history analytics error: {e}")
            return {
                "time_range": time_range,
                "country_filter": country,
                "isp_filter": isp,
                "performance_trends": [],
                "geo_distribution": [],
                "isp_distribution": [],
                "error": str(e)
            }
    
    async def get_proxy_quality_stats(self, proxy_id: Optional[str] = None) -> Dict[str, Any]:
        """获取代理质量统计"""
        try:
            if proxy_id:
                # 获取特定代理的详细统计
                proxy_query = f"""
                    SELECT 
                        p.*,
                        pq.quality_score,
                        pq.total_usage,
                        pq.success_count
                    FROM proxies p
                    LEFT JOIN proxy_qualities pq ON p.id = pq.proxy_id
                    WHERE p.id = '{proxy_id}'
                """
                
                usage_query = f"""
                    SELECT 
                        COUNT(*) as total_usage,
                        SUM(CASE WHEN success = 'SUCCESS' THEN 1 ELSE 0 END) as successful_usage,
                        AVG(response_time) as avg_response_time,
                        AVG(latency) as avg_latency,
                        MIN(created_at) as first_used,
                        MAX(created_at) as last_used
                    FROM proxy_usage_history 
                    WHERE proxy_id = '{proxy_id}'
                """
                
                proxy_info = await data_connector.query_external_db("proxy_db", proxy_query)
                usage_stats = await data_connector.query_external_db("proxy_db", usage_query)
                
                if not proxy_info:
                    return {"error": "Proxy not found"}
                
                return {
                    "proxy_info": proxy_info[0],
                    "usage_stats": usage_stats[0] if usage_stats else {}
                }
            else:
                # 获取所有代理的汇总统计
                summary_query = """
                    SELECT 
                        COUNT(*) as total_proxies,
                        COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as active_proxies,
                        AVG(success_rate) as avg_success_rate,
                        AVG(latency) as avg_latency,
                        COUNT(DISTINCT country) as unique_countries,
                        COUNT(DISTINCT isp) as unique_isps
                    FROM proxies
                """
                
                quality_query = """
                    SELECT 
                        quality_score,
                        COUNT(*) as count
                    FROM proxy_qualities
                    GROUP BY quality_score
                    ORDER BY quality_score
                """
                
                summary = await data_connector.query_external_db("proxy_db", summary_query)
                quality_dist = await data_connector.query_external_db("proxy_db", quality_query)
                
                return {
                    "summary": summary[0] if summary else {},
                    "quality_distribution": quality_dist
                }
                
        except Exception as e:
            print(f"Proxy quality stats error: {e}")
            return {"error": str(e)}


# 全局代理分析服务实例
proxy_analysis_service = ProxyAnalysisService()