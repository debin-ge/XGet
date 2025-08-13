from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, TypeVar, Generic
from datetime import datetime
import math

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """通用分页响应模式"""
    items: List[T] = Field(description="数据列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    size: int = Field(description="每页大小")
    pages: int = Field(description="总页数")

    @classmethod
    def create(cls, items: List[T], total: int, page: int, size: int):
        """创建分页响应"""
        pages = math.ceil(total / size) if total > 0 else 1
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )


class AccountBase(BaseModel):
    username: str
    email: str
    login_method: str = "TWITTER"


class AccountCreate(AccountBase):
    password: str
    email_password: Optional[str] = None


class AccountUpdate(BaseModel):
    email: Optional[str] = None
    email_password: Optional[str] = None
    proxy_id: Optional[str] = None
    active: Optional[bool] = None
    user_agent: Optional[str] = None


class AccountResponse(AccountBase):
    id: str
    active: bool
    proxy_id: Optional[str] = None
    last_used: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    error_msg: Optional[str] = None
    cookies: Optional[Dict] = None
    headers: Optional[Dict] = None
    user_agent: Optional[str] = None

    class Config:
        from_attributes = True


class AccountLogin(BaseModel):
    proxy_id: Optional[str] = None
    async_login: bool = False


class AccountLoginResponse(BaseModel):
    id: str
    username: str
    active: bool
    login_successful: bool
    cookies_obtained: bool
    last_used: Optional[datetime] = None
    message: Optional[str] = None


class AccountListResponse(PaginatedResponse[AccountResponse]):
    """账户分页响应"""
    pass
