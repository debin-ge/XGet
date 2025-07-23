from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LoginHistoryResponse(BaseModel):
    id: str
    account_id: str
    proxy_id: Optional[str] = None
    login_time: datetime
    status: str
    error_msg: Optional[str] = None
    cookies_count: int
    response_time: Optional[int] = None
    
    class Config:
        from_attributes = True 