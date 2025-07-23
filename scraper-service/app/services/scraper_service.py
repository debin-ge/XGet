from typing import List, Optional, Dict, Any
from ..db.database import mongodb
from ..models.result import RESULT_TYPE_TWEET, RESULT_TYPE_USER, RESULT_TYPE_TOPIC, RESULT_TYPE_FOLLOWER
from ..schemas.result import ResultCreate
import uuid
from datetime import datetime


class ScraperService:
    def __init__(self):
        self.results_collection = mongodb.results

    async def save_result(self, result_data: ResultCreate) -> Dict:
        """保存采集结果"""
        result = {
            "id": str(uuid.uuid4()),
            "task_id": result_data.task_id,
            "data_type": result_data.data_type,
            "data": result_data.data,
            "metadata": result_data.metadata or {},
            "created_at": datetime.now()
        }
        
        await self.results_collection.insert_one(result)
        return result

    async def save_results(self, results_data: List[ResultCreate]) -> List[Dict]:
        """批量保存采集结果"""
        if not results_data:
            return []
            
        results = []
        for result_data in results_data:
            result = {
                "id": str(uuid.uuid4()),
                "task_id": result_data.task_id,
                "data_type": result_data.data_type,
                "data": result_data.data,
                "metadata": result_data.metadata or {},
                "created_at": datetime.now()
            }
            results.append(result)
            
        if results:
            await self.results_collection.insert_many(results)
            
        return results

    async def get_results(
        self,
        task_id: Optional[str] = None,
        data_type: Optional[str] = None,
        query: Optional[Dict] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict:
        """获取采集结果"""
        filter_query = {}
        
        if task_id:
            filter_query["task_id"] = task_id
        if data_type:
            filter_query["data_type"] = data_type
        if query:
            for key, value in query.items():
                if key.startswith("data."):
                    filter_query[key] = value
                else:
                    filter_query[f"data.{key}"] = value
                    
        total = await self.results_collection.count_documents(filter_query)
        
        cursor = self.results_collection.find(filter_query).skip(skip).limit(limit).sort("created_at", -1)
        results = await cursor.to_list(length=limit)
        
        return {
            "total": total,
            "data": results
        }

    async def get_result(self, result_id: str) -> Optional[Dict]:
        """获取单个结果"""
        result = await self.results_collection.find_one({"id": result_id})
        return result

    async def delete_results(self, task_id: str) -> int:
        """删除任务相关的所有结果"""
        result = await self.results_collection.delete_many({"task_id": task_id})
        return result.deleted_count