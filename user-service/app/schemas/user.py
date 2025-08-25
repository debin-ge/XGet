from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """通用分页响应模式"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    
    @classmethod
    def create(cls, items: List[T], total: int, page: int, size: int):
        """创建分页响应"""
        pages = (total + size - 1) // size if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )


class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"


class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c.isalpha() for c in v):
            raise ValueError('Password must contain at least one letter')
        return v


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c.isalpha() for c in v):
            raise ValueError('Password must contain at least one letter')
        return v


class UserInDB(UserBase):
    id: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    last_login: Optional[datetime] = None
    failed_login_attempts: int
    locked_until: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = {}
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class User(UserInDB):
    pass


class UserWithRoles(User):
    roles: Optional[List[str]] = []


class UserPreferences(BaseModel):
    theme: str = "light"
    notifications: Dict[str, bool] = {
        "email": True,
        "push": False,
        "sms": False
    }
    privacy: Dict[str, bool] = {
        "profile_visible": True,
        "activity_visible": True
    }
    display: Dict[str, Any] = {
        "items_per_page": 20,
        "sort_order": "desc"
    }


class UserLogin(BaseModel):
    username: str
    password: str


class UserLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User


class TokenRefresh(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserStatus(BaseModel):
    is_active: bool
    is_verified: bool
    is_locked: bool
    locked_until: Optional[datetime] = None
    failed_attempts: int


class UserListResponse(PaginatedResponse[User]):
    """用户列表分页响应"""
    pass 