import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import func, text, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging

from app.models.account import Account
from app.models.login_history import LoginHistory
from app.schemas.analytics import (
    AnalyticsResponse,
    RealtimeAnalyticsData,
    HistoryAnalyticsData,
    AccountUsageStats,
    AccountSummaryStats,
    HealthMetrics,
    LoginTrendData,
    RecentActivity,
    ActivityType
)
from app.core.redis import RedisManager

logger = logging.getLogger(__name__)


class AccountAnalyticsService:
    """账户分析服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache_ttl = 300  # 5分钟缓存
    
    def _get_cache_key(self, prefix: str, *args) -> str:
        """生成缓存键"""
        return f"account_analytics:{prefix}:{':'.join(str(arg) for arg in args if arg is not None)}"
    
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
            await RedisManager.set_json(key, data, ttl)
        except Exception as e:
            logger.warning(f"缓存设置失败 {key}: {e}")
    
    async def get_realtime_analytics(self) -> AnalyticsResponse:
        """获取实时账户分析数据"""
        cache_key = self._get_cache_key("realtime")
        
        # 尝试从缓存获取
        cached_data = await self._get_from_cache(cache_key)
        if cached_data:
            return AnalyticsResponse(**cached_data)
        
        try:
            # 获取活跃账户数
            active_accounts_query = await self.db.execute(
                text("""
                    SELECT COUNT(*) as count 
                    FROM accounts 
                    WHERE active = TRUE AND is_deleted = FALSE
                """)
            )
            active_accounts = active_accounts_query.scalar() or 0
            
            # 获取最近1小时的登录统计
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            login_stats_query = await self.db.execute(
                text("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as success,
                        AVG(response_time) as avg_response_time
                    FROM login_history 
                    WHERE login_time >= :start_time
                """),
                {"start_time": one_hour_ago}
            )
            login_stats = login_stats_query.fetchone()
            
            total_logins = login_stats.total or 0
            successful_logins = login_stats.success or 0
            avg_response_time = float(login_stats.avg_response_time or 0) / 1000  # 转换为秒
            
            # 计算成功率
            login_success_rate = successful_logins / total_logins if total_logins > 0 else 0.0
            
            # 构建响应数据
            realtime_data = RealtimeAnalyticsData(
                active_accounts=active_accounts,
                login_success_rate=login_success_rate,
                avg_response_time=avg_response_time,
                last_updated=datetime.utcnow()
            )
            
            response_data = {
                "success": True,
                "message": "实时账户分析数据获取成功",
                "data": realtime_data.model_dump()
            }
            
            # 缓存数据
            await self._set_cache(cache_key, response_data)
            
            return AnalyticsResponse(**response_data)
            
        except Exception as e:
            logger.error(f"获取实时账户分析数据失败: {e}")
            return AnalyticsResponse(
                success=False,
                message=f"获取实时账户分析数据失败: {str(e)}"
            )
    
    async def get_history_analytics(self, time_range: str = "24h") -> AnalyticsResponse:
        """获取历史账户分析数据"""
        cache_key = self._get_cache_key("history", time_range)
        
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
            
            # 获取趋势数据
            trends_query = await self.db.execute(
                text("""
                    SELECT 
                        DATE_TRUNC('hour', login_time) as time_bucket,
                        COUNT(*) as total_logins,
                        SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful_logins,
                        AVG(response_time) as avg_response_time
                    FROM login_history 
                    WHERE login_time >= :start_time
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                """),
                {"start_time": start_time}
            )
            trends_data = trends_query.fetchall()
            
            # 构建趋势数据
            trends = []
            for row in trends_data:
                total_logins = row.total_logins or 0
                successful_logins = row.successful_logins or 0
                success_rate = successful_logins / total_logins if total_logins > 0 else 0.0
                
                trend_item = LoginTrendData(
                    time_bucket=row.time_bucket,
                    total_logins=total_logins,
                    successful_logins=successful_logins,
                    failed_logins=total_logins - successful_logins,
                    success_rate=success_rate,
                    avg_response_time=float(row.avg_response_time or 0) / 1000
                )
                trends.append(trend_item.model_dump())
            
            # 获取健康度指标
            health_metrics_query = await self.db.execute(
                text("""
                    SELECT 
                        COUNT(*) as total_accounts,
                        SUM(CASE WHEN active = TRUE THEN 1 ELSE 0 END) as active_accounts,
                        SUM(CASE WHEN error_msg IS NOT NULL AND error_msg != '' THEN 1 ELSE 0 END) as error_accounts
                    FROM accounts 
                    WHERE is_deleted = FALSE
                """)
            )
            health_metrics_data = health_metrics_query.fetchone()
            
            total_accounts = health_metrics_data.total_accounts or 0
            active_accounts = health_metrics_data.active_accounts or 0
            error_accounts = health_metrics_data.error_accounts or 0
            
            # 计算健康度分数
            health_score = self._calculate_health_score({
                "total_accounts": total_accounts,
                "active_accounts": active_accounts,
                "error_accounts": error_accounts
            })
            
            health_metrics = HealthMetrics(
                total_accounts=total_accounts,
                active_accounts=active_accounts,
                error_accounts=error_accounts,
                health_score=health_score
            )
            
            history_data = HistoryAnalyticsData(
                time_range=time_range,
                trends=trends,
                health_metrics=health_metrics.model_dump()
            )
            
            response_data = {
                "success": True,
                "message": "历史账户分析数据获取成功",
                "data": history_data.model_dump()
            }
            
            # 缓存数据
            await self._set_cache(cache_key, response_data)
            
            return AnalyticsResponse(**response_data)
            
        except Exception as e:
            logger.error(f"获取历史账户分析数据失败: {e}")
            return AnalyticsResponse(
                success=False,
                message=f"获取历史账户分析数据失败: {str(e)}"
            )
    
    async def get_account_usage_stats(self, account_id: Optional[str] = None) -> AnalyticsResponse:
        """获取账户使用统计"""
        cache_key = self._get_cache_key("usage", account_id or "all")
        
        # 尝试从缓存获取
        cached_data = await self._get_from_cache(cache_key)
        if cached_data:
            return AnalyticsResponse(**cached_data)
        
        try:
            if account_id:
                # 获取指定账户的详细统计
                account_stats_query = await self.db.execute(
                    text("""
                        SELECT 
                            a.id,
                            a.username,
                            a.active,
                            COUNT(lh.id) as total_logins,
                            SUM(CASE WHEN lh.status = 'SUCCESS' THEN 1 ELSE 0 END) as successful_logins,
                            AVG(CASE WHEN lh.response_time > 0 THEN lh.response_time END) as avg_response_time,
                            MAX(lh.login_time) as last_login_time
                        FROM accounts a
                        LEFT JOIN login_history lh ON a.id = lh.account_id
                        WHERE a.id = :account_id AND a.is_deleted = FALSE
                        GROUP BY a.id, a.username, a.active
                    """),
                    {"account_id": account_id}
                )
                account_stats = account_stats_query.fetchone()
                
                if not account_stats:
                    return AnalyticsResponse(
                        success=False,
                        message="账户不存在"
                    )
                
                total_logins = account_stats.total_logins or 0
                successful_logins = account_stats.successful_logins or 0
                failed_logins = total_logins - successful_logins
                success_rate = successful_logins / total_logins if total_logins > 0 else 0.0
                avg_response_time = float(account_stats.avg_response_time or 0) / 1000
                
                # 计算距离最后登录天数
                days_since_last_login = None
                if account_stats.last_login_time:
                    days_since_last_login = (datetime.utcnow() - account_stats.last_login_time).days
                
                usage_stats = AccountUsageStats(
                    account_id=account_stats.id,
                    username=account_stats.username,
                    total_logins=total_logins,
                    successful_logins=successful_logins,
                    failed_logins=failed_logins,
                    success_rate=success_rate,
                    avg_response_time=avg_response_time,
                    last_login_time=account_stats.last_login_time,
                    days_since_last_login=days_since_last_login
                )
                
                message = f"账户 {account_stats.username} 的使用统计获取成功"
                
            else:
                # 获取所有账户的汇总统计
                summary_stats_query = await self.db.execute(
                    text("""
                        SELECT 
                            COUNT(*) as total_accounts,
                            SUM(CASE WHEN active = TRUE THEN 1 ELSE 0 END) as active_accounts,
                            SUM(CASE WHEN error_msg IS NOT NULL AND error_msg != '' THEN 1 ELSE 0 END) as error_accounts
                        FROM accounts 
                        WHERE is_deleted = FALSE
                    """)
                )
                summary_data = summary_stats_query.fetchone()
                
                # 获取登录统计
                login_stats_query = await self.db.execute(
                    text("""
                        SELECT 
                            COUNT(*) as total_logins,
                            SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful_logins,
                            AVG(response_time) as avg_response_time
                        FROM login_history
                    """)
                )
                login_stats = login_stats_query.fetchone()
                
                total_accounts = summary_data.total_accounts or 0
                active_accounts = summary_data.active_accounts or 0
                inactive_accounts = total_accounts - active_accounts
                accounts_with_errors = summary_data.error_accounts or 0
                
                total_logins = login_stats.total_logins or 0
                successful_logins = login_stats.successful_logins or 0
                average_success_rate = successful_logins / total_logins if total_logins > 0 else 0.0
                average_response_time = float(login_stats.avg_response_time or 0) / 1000
                
                usage_stats = AccountSummaryStats(
                    total_accounts=total_accounts,
                    active_accounts=active_accounts,
                    inactive_accounts=inactive_accounts,
                    accounts_with_errors=accounts_with_errors,
                    average_success_rate=average_success_rate,
                    average_response_time=average_response_time,
                    inactive_days_threshold=7  # 默认7天为非活跃
                )
                
                message = "账户使用汇总统计获取成功"
            
            response_data = {
                "success": True,
                "message": message,
                "data": usage_stats.model_dump()
            }
            
            # 缓存数据
            await self._set_cache(cache_key, response_data)
            
            return AnalyticsResponse(**response_data)
            
        except Exception as e:
            logger.error(f"获取账户使用统计失败: {e}")
            return AnalyticsResponse(
                success=False,
                message=f"获取账户使用统计失败: {str(e)}"
            )
    
    def _calculate_health_score(self, health_data: Dict[str, int]) -> float:
        """计算健康度分数"""
        try:
            total_accounts = health_data.get("total_accounts", 0)
            active_accounts = health_data.get("active_accounts", 0)
            error_accounts = health_data.get("error_accounts", 0)
            
            if total_accounts == 0:
                return 0.0
            
            # 计算活跃率
            active_ratio = active_accounts / total_accounts
            
            # 计算错误率
            error_ratio = error_accounts / total_accounts if total_accounts > 0 else 0
            
            # 健康度公式：活跃率 * (1 - 错误率) * 100
            health_score = active_ratio * (1 - error_ratio) * 100
            
            return round(health_score, 2)
            
        except Exception as e:
            logger.error(f"计算健康度分数失败: {e}")
            return 0.0
    
    async def get_recent_account_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的账户相关活动"""
        try:
            # 获取最近的登录历史作为账户活动
            activities_query = await self.db.execute(
                text("""
                    SELECT 
                        lh.id,
                        lh.account_id,
                        a.username,
                        lh.login_time as timestamp,
                        lh.status,
                        lh.error_msg,
                        lh.response_time,
                        lh.proxy_id
                    FROM login_history lh
                    JOIN accounts a ON lh.account_id = a.id
                    WHERE a.is_deleted = FALSE
                    ORDER BY lh.login_time DESC
                    LIMIT :limit
                """),
                {"limit": limit}
            )
            activities_data = activities_query.fetchall()
            
            activities = []
            for row in activities_data:
                # 构建活动描述
                if row.status == 'SUCCESS':
                    description = f"账户 {row.username} 登录成功"
                    status = "success"
                else:
                    description = f"账户 {row.username} 登录失败"
                    status = "error"
                
                # 构建详情
                details = {
                    "account_id": row.account_id,
                    "username": row.username,
                    "proxy_id": row.proxy_id,
                    "response_time": row.response_time,
                    "error_message": row.error_msg
                }
                
                activity = RecentActivity(
                    id=str(row.id),
                    type=ActivityType.ACCOUNT_LOGIN,
                    timestamp=row.timestamp,
                    description=description,
                    status=status,
                    details=details,
                    service="account-service"
                )
                activities.append(activity.model_dump())
            
            return activities
            
        except Exception as e:
            logger.error(f"获取最近账户活动失败: {e}")
            return []
    
    async def invalidate_analytics_cache(self):
        """清除分析缓存"""
        try:
            # 获取所有account_analytics相关的键
            pattern = "account_analytics:*"
            deleted_count = await RedisManager.delete_keys(pattern)
            logger.info(f"清除了 {deleted_count} 个分析缓存键")
            
        except Exception as e:
            logger.error(f"清除分析缓存失败: {e}")