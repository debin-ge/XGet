from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_connector import data_connector
from app.core.cache import cache_response
from app.core.config import settings


class AccountAnalysisService:
    """账户分析服务"""
    
    @cache_response(expire=settings.CACHE_TTL, key_prefix="analytics:accounts:realtime")
    async def get_realtime_analytics(self) -> Dict[str, Any]:
        """获取账户实时统计数据"""
        try:
            # 从account_db获取实时数据
            active_accounts_query = """
                SELECT COUNT(*) as count 
                FROM accounts 
                WHERE active = TRUE AND is_deleted = FALSE
            """
            
            login_success_query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as success
                FROM login_history 
                WHERE login_time >= NOW() - INTERVAL '1 hour'
            """
            
            response_time_query = """
                SELECT AVG(response_time) as avg_response_time
                FROM login_history 
                WHERE response_time IS NOT NULL 
                AND login_time >= NOW() - INTERVAL '1 hour'
            """
            
            # 执行查询
            active_accounts = await data_connector.query_external_db("account_db", active_accounts_query)
            login_stats = await data_connector.query_external_db("account_db", login_success_query)
            response_time = await data_connector.query_external_db("account_db", response_time_query)
            
            # 计算指标
            active_count = active_accounts[0]['count'] if active_accounts else 0
            
            if login_stats and login_stats[0]['total'] > 0:
                success_rate = (login_stats[0]['success'] / login_stats[0]['total']) * 100
            else:
                success_rate = 0.0
            
            avg_response_time = response_time[0]['avg_response_time'] if response_time and response_time[0]['avg_response_time'] else 0.0
            
            return {
                "active_accounts": active_count,
                "login_success_rate": round(success_rate, 2),
                "avg_response_time": round(avg_response_time, 2) if avg_response_time is not None else 0.0,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Account realtime analytics error: {e}")
            return {
                "active_accounts": 0,
                "login_success_rate": 0.0,
                "avg_response_time": 0.0,
                "last_updated": datetime.now().isoformat(),
                "error": str(e)
            }
    
    @cache_response(expire=settings.CACHE_TTL, key_prefix="analytics:accounts:history")
    async def get_history_analytics(self, time_range: str = "24h") -> Dict[str, Any]:
        """获取账户历史统计数据"""
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
            
            # 构建历史趋势查询
            trend_query = f"""
                SELECT 
                    DATE_TRUNC('hour', login_time) as time_bucket,
                    COUNT(*) as total_logins,
                    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful_logins,
                    AVG(response_time) as avg_response_time
                FROM login_history 
                WHERE login_time >= NOW() - INTERVAL '{interval}'
                GROUP BY time_bucket
                ORDER BY time_bucket
            """
            
            # 执行查询
            trend_data = await data_connector.query_external_db("account_db", trend_query)
            
            # 处理趋势数据
            trends = []
            for row in trend_data:
                success_rate = (row['successful_logins'] / row['total_logins'] * 100) if row['total_logins'] > 0 else 0
                trends.append({
                    "timestamp": row['time_bucket'].isoformat(),
                    "total_logins": row['total_logins'],
                    "successful_logins": row['successful_logins'],
                    "success_rate": round(success_rate, 2),
                    "avg_response_time": round(row['avg_response_time'], 2) if row['avg_response_time'] is not None else 0.0
                })
            
            # 获取账户健康度统计
            health_query = """
                SELECT 
                    COUNT(*) as total_accounts,
                    SUM(CASE WHEN active = TRUE THEN 1 ELSE 0 END) as active_accounts,
                    SUM(CASE WHEN error_msg IS NOT NULL THEN 1 ELSE 0 END) as error_accounts
                FROM accounts 
                WHERE is_deleted = FALSE
            """
            
            health_stats = await data_connector.query_external_db("account_db", health_query)
            
            health_data = health_stats[0] if health_stats else {}
            
            return {
                "time_range": time_range,
                "trends": trends,
                "health_metrics": {
                    "total_accounts": health_data.get('total_accounts', 0),
                    "active_accounts": health_data.get('active_accounts', 0),
                    "error_accounts": health_data.get('error_accounts', 0),
                    "health_score": self._calculate_health_score(health_data)
                },
            }
            
        except Exception as e:
            print(f"Account history analytics error: {e}")
            return {
                "time_range": time_range,
                "trends": [],
                "health_metrics": {},
                "error": str(e)
            }
    
    def _calculate_health_score(self, health_data: Dict[str, Any]) -> float:
        """计算账户健康度评分"""
        total = health_data.get('total_accounts', 0)
        active = health_data.get('active_accounts', 0)
        errors = health_data.get('error_accounts', 0)
        
        if total == 0:
            return 0.0
        
        # 基础评分公式：活跃账户比例 * (1 - 错误账户比例)
        active_ratio = active / total
        error_ratio = errors / total if total > 0 else 0
        
        score = active_ratio * (1 - error_ratio) * 100
        return round(score, 2)
    
    async def get_account_usage_stats(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """获取账户使用统计"""
        try:
            if account_id:
                # 获取特定账户的详细统计
                account_query = f"""
                    SELECT 
                        username,
                        email,
                        active,
                        last_used,
                        error_msg,
                        created_at
                    FROM accounts 
                    WHERE id = '{account_id}' AND is_deleted = FALSE
                """
                
                usage_query = f"""
                    SELECT 
                        COUNT(*) as total_logins,
                        SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful_logins,
                        AVG(response_time) as avg_response_time,
                        MAX(login_time) as last_login
                    FROM login_history 
                    WHERE account_id = '{account_id}'
                """
                
                account_info = await data_connector.query_external_db("account_db", account_query)
                usage_stats = await data_connector.query_external_db("account_db", usage_query)
                
                if not account_info:
                    return {"error": "Account not found"}
                
                return {
                    "account_info": account_info[0],
                    "usage_stats": usage_stats[0] if usage_stats else {}
                }
            else:
                # 获取所有账户的汇总统计
                summary_query = """
                    SELECT 
                        COUNT(*) as total_accounts,
                        COUNT(CASE WHEN active = TRUE THEN 1 END) as active_accounts,
                        COUNT(CASE WHEN error_msg IS NOT NULL THEN 1 END) as problematic_accounts,
                        AVG(EXTRACT(EPOCH FROM (NOW() - last_used))) as avg_inactivity_seconds
                    FROM accounts 
                    WHERE is_deleted = FALSE
                """
                
                summary = await data_connector.query_external_db("account_db", summary_query)
                return summary[0] if summary else {}
                
        except Exception as e:
            print(f"Account usage stats error: {e}")
            return {"error": str(e)}


# 全局账户分析服务实例
account_analysis_service = AccountAnalysisService()