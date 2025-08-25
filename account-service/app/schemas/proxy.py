from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Proxy(BaseModel):
    id: str
    ip: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    type: str
    latency: Optional[int] = None
    success_rate: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None