from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4

class StorageOptions(BaseModel):
    """存储选项模型"""
    compression: bool = True
    encryption: bool = False
    replication: int = 1

class StorageRequest(BaseModel):
    """存储请求模型"""
    data_type: str
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    storage_options: Optional[StorageOptions] = None
    
    @validator('storage_options', pre=True, always=True)
    def set_storage_options(cls, v):
        return v or StorageOptions()

class BatchStorageRequest(BaseModel):
    """批量存储请求模型"""
    items: List[StorageRequest]

class StorageResponse(BaseModel):
    """存储响应模型"""
    id: str
    data_type: str
    size: int
    storage_location: str
    storage_backend: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

class StorageSearchQuery(BaseModel):
    """存储搜索查询模型"""
    must: Optional[List[Dict[str, Any]]] = None
    should: Optional[List[Dict[str, Any]]] = None
    must_not: Optional[List[Dict[str, Any]]] = None
    filter: Optional[List[Dict[str, Any]]] = None
    
class StorageSearchRequest(BaseModel):
    """存储高级搜索请求模型"""
    query: StorageSearchQuery
    sort: Optional[List[Dict[str, str]]] = None
    limit: int = 20
    offset: int = 0

class StorageSearchResponse(BaseModel):
    """存储搜索响应模型"""
    items: List[StorageResponse]
    total: int
    limit: int
    offset: int

class StorageStatsResponse(BaseModel):
    """存储统计响应模型"""
    total_items: int
    total_size: int
    by_data_type: Dict[str, Dict[str, Union[int, float]]]
    by_storage_backend: Dict[str, Dict[str, Union[int, float]]]
    by_status: Dict[str, int] 