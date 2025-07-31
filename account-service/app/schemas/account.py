from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


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
