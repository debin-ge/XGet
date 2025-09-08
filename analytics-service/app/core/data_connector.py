import httpx
from typing import Dict, Any, List, Optional
import motor.motor_asyncio
from pymongo import MongoClient
import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings


class DataConnector:
    """多数据源连接器"""
    
    def __init__(self):
        self.mongo_client = None
        self.external_pools = {}  # 数据库连接池字典
        self.connected_dbs = set()  # 已连接的数据库
    
    async def connect_mongodb(self):
        """连接MongoDB数据库"""
        if self.mongo_client:
            return True
            
        try:
            self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URI)
            self.mongo_db = self.mongo_client[settings.MONGODB_DB]
            # Test connection
            await self.mongo_db.command('ping')
            print("MongoDB connection established successfully")
            return True
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            return False
    
    async def get_external_pool(self, db_name: str):
        """获取或创建外部数据库连接池"""
        if db_name in self.external_pools:
            return self.external_pools[db_name]
            
        try:
            # 创建新的连接池
            pool = await asyncpg.create_pool(
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                host=settings.POSTGRES_SERVER,
                port=5432,
                database=db_name,
                min_size=1,
                max_size=10
            )
            self.external_pools[db_name] = pool
            self.connected_dbs.add(db_name)
            print(f"Connection pool created for database: {db_name}")
            return pool
        except Exception as e:
            print(f"Failed to create connection pool for {db_name}: {e}")
            return None
    
    async def query_external_db(self, db_name: str, query: str, params: Optional[Dict] = None):
        """查询外部数据库"""
        pool = await self.get_external_pool(db_name)
        if not pool:
            return []
            
        try:
            async with pool.acquire() as conn:
                if params:
                    result = await conn.fetch(query, *params.values())
                else:
                    result = await conn.fetch(query)
                return [dict(row) for row in result]
        except Exception as e:
            print(f"Query failed for {db_name}: {e}")
            return []
    
    async def execute_external_db(self, db_name: str, query: str, params: Optional[Dict] = None):
        """执行外部数据库操作"""
        pool = await self.get_external_pool(db_name)
        if not pool:
            return False
            
        try:
            async with pool.acquire() as conn:
                if params:
                    await conn.execute(query, *params.values())
                else:
                    await conn.execute(query)
                return True
        except Exception as e:
            print(f"Execute failed for {db_name}: {e}")
            return False
    
    async def get_mongodb_client(self):
        """获取MongoDB客户端实例"""
        if not self.mongo_client:
            await self.connect_mongodb()
        return self.mongo_client
    
    def get_mongodb_database(self):
        """获取MongoDB数据库实例"""
        if self.mongo_client:
            return self.mongo_db
        return None
    
    async def close_connections(self):
        """关闭所有连接"""
        # 关闭MongoDB连接
        if self.mongo_client:
            self.mongo_client.close()
        
        # 关闭所有PostgreSQL连接池
        for db_name, pool in self.external_pools.items():
            await pool.close()
            print(f"Closed connection pool for database: {db_name}")
        
        self.external_pools.clear()
        self.connected_dbs.clear()
        self.mongo_client = None


# 全局数据连接器实例
data_connector = DataConnector()


async def init_data_connections():
    """初始化所有数据连接"""
    # 连接MongoDB
    mongo_connected = await data_connector.connect_mongodb()
    
    # 预连接常用外部数据库
    dbs_to_preconnect = ["account_db", "proxy_db", "scraper_db", "user_db"]
    
    for db_name in dbs_to_preconnect:
        pool = await data_connector.get_external_pool(db_name)
        if pool:
            print(f"Pre-connected to external database: {db_name}")
        else:
            print(f"Failed to pre-connect to external database: {db_name}")
    
    return mongo_connected