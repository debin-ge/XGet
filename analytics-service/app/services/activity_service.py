from typing import List, Dict, Any
from datetime import datetime
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.config import settings
from app.schemas.analytics import RecentActivity, ActivityType


class ActivityService:
    """Service for fetching recent activities across all services"""
    
    def __init__(self):
        self.db_configs = {
            'account_db': {
                'url': f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}/account_db"
            },
            'proxy_db': {
                'url': f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}/proxy_db"
            },
            'scraper_db': {
                'url': f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}/scraper_db"
            }
        }
    
    async def get_recent_activities(self, limit: int = 10) -> List[RecentActivity]:
        """Get recent activities from all services"""
        # Fetch activities from all databases concurrently
        tasks = [
            self._get_account_activities(limit),
            self._get_proxy_activities(limit),
            self._get_task_activities(limit)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and sort all activities
        all_activities = []
        for result in results:
            if not isinstance(result, Exception) and result:
                all_activities.extend(result)
        
        # Sort by timestamp descending
        all_activities.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Return top N activities
        return all_activities[:limit]
    
    async def _get_account_activities(self, limit: int) -> List[RecentActivity]:
        """Get recent account login activities"""
        try:
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            
            # Create connection to account_db
            account_db_url = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}/account_db"
            engine = create_async_engine(account_db_url)
            AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            async with AsyncSessionLocal() as db:
                result = await db.execute(text("""
                    SELECT id, account_id, login_time, status, error_msg, response_time, cookies_count
                    FROM login_history 
                    ORDER BY login_time DESC 
                    LIMIT :limit
                """), {"limit": limit})
                
                activities = []
                for row in result:
                    activity = RecentActivity(
                        id=str(row[0]),
                        type=ActivityType.ACCOUNT_LOGIN,
                        timestamp=row[2],
                        description=f"Account login: {row[1]}",
                        status=row[3],
                        details={
                            "account_id": row[1],
                            "error_message": row[4],
                            "response_time": float(row[5]) if row[5] else 0.0,
                            "cookies_count": row[6]
                        },
                        service="account"
                    )
                    activities.append(activity)
                
                await engine.dispose()
                return activities
                
        except Exception as e:
            print(f"Error fetching account activities: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def _get_proxy_activities(self, limit: int) -> List[RecentActivity]:
        """Get recent proxy usage activities"""
        try:
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            
            # Create connection to proxy_db
            proxy_db_url = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}/proxy_db"
            engine = create_async_engine(proxy_db_url)
            AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            async with AsyncSessionLocal() as db:
                result = await db.execute(text("""
                    SELECT id, proxy_id, account_id, task_id, service_name, success, 
                           response_time, created_at, account_username_email, task_name
                    FROM proxy_usage_history 
                    ORDER BY created_at DESC 
                    LIMIT :limit
                """), {"limit": limit})
                
                activities = []
                for row in result:
                    activity = RecentActivity(
                        id=str(row[0]),
                        type=ActivityType.PROXY_USAGE,
                        timestamp=row[7],
                        description=f"Proxy usage: {row[4]} service",
                        status="SUCCESS" if row[5] == "true" else "FAILED",
                        details={
                            "proxy_id": row[1],
                            "account_id": row[2],
                            "task_id": row[3],
                            "service_name": row[4],
                            "response_time": float(row[6]) if row[6] else 0.0,
                            "account_username": row[8],
                            "task_name": row[9]
                        },
                        service="proxy"
                    )
                    activities.append(activity)
                
                await engine.dispose()
                return activities
                
        except Exception as e:
            print(f"Error fetching proxy activities: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def _get_task_activities(self, limit: int) -> List[RecentActivity]:
        """Get recent task execution activities"""
        try:
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            
            # Create connection to scraper_db
            scraper_db_url = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}/scraper_db"
            engine = create_async_engine(scraper_db_url)
            AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            async with AsyncSessionLocal() as db:
                result = await db.execute(text("""
                    SELECT id, task_id, account_id, proxy_id, status, started_at, 
                           completed_at, duration, error_message
                    FROM task_executions 
                    ORDER BY started_at DESC 
                    LIMIT :limit
                """), {"limit": limit})
                
                activities = []
                for row in result:
                    activity = RecentActivity(
                        id=str(row[0]),
                        type=ActivityType.TASK_EXECUTION,
                        timestamp=row[5] or datetime.utcnow(),
                        description=f"Task execution: {row[1]}",
                        status=row[4],
                        details={
                            "task_id": row[1],
                            "account_id": row[2],
                            "proxy_id": row[3],
                            "started_at": row[5],
                            "completed_at": row[6],
                            "duration": float(row[7]) if row[7] else 0.0,
                            "error_message": row[8]
                        },
                        service="scraper"
                    )
                    activities.append(activity)
                
                await engine.dispose()
                return activities
                
        except Exception as e:
            print(f"Error fetching task activities: {e}")
            import traceback
            traceback.print_exc()
            return []


# Global instance
activity_service = ActivityService()