from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .account import PaginatedResponse

class LoginHistoryResponse(BaseModel):
    id: str
    account_id: str
    proxy_id: Optional[str] = None
    status: str  # SUCCESS, FAILED
    error_msg: Optional[str] = None
    cookies_count: int = 0
    response_time: Optional[int] = None  # milliseconds
    login_time: datetime
    
    class Config:
        from_attributes = True 

class LoginHistoryListResponse(PaginatedResponse[LoginHistoryResponse]):
    """登录历史分页响应"""
    pass 