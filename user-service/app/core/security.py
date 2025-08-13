from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..models.user import User
from ..models.role import Role, Permission
from .config import settings
import redis
import json
from .logging import logger

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer token
security = HTTPBearer()

# Redis连接
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希值"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """验证令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # 检查令牌是否在黑名单中
    if redis_client.get(f"blacklist:{token}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive"
        )
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def check_permission(permission: str):
    """检查权限装饰器"""
    def permission_checker(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        user_permissions = get_user_permissions(current_user, db)
        logger.info(f"User permissions: {user_permissions}")
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return permission_checker


def get_user_permissions(user: User, db: Session) -> set:
    """获取用户权限"""
    cache_key = f"user_permissions:{user.id}"
    
    # 尝试从缓存获取
    cached_permissions = redis_client.get(cache_key)
    if cached_permissions:
        return set(json.loads(cached_permissions))
    
    # 从数据库获取权限
    permissions = set()
    for user_role in user.roles:
        if user_role.is_active and user_role.role:
            for permission in user_role.role.permissions:
                if permission.is_active:
                    permissions.add(f"{permission.resource}:{permission.action}")
    
    # 缓存权限（5分钟）
    redis_client.setex(cache_key, 300, json.dumps(list(permissions)))
    return permissions


def revoke_token(token: str) -> bool:
    """撤销令牌"""
    try:
        payload = verify_token(token)
        exp = payload.get("exp")
        if exp:
            # 计算剩余时间
            remaining_time = exp - datetime.utcnow().timestamp()
            if remaining_time > 0:
                redis_client.setex(f"blacklist:{token}", int(remaining_time), "1")
                return True
    except:
        pass
    return False


def is_token_revoked(token: str) -> bool:
    """检查令牌是否被撤销"""
    return bool(redis_client.get(f"blacklist:{token}"))


def increment_login_attempts(user_id: str) -> int:
    """增加登录尝试次数"""
    key = f"login_attempts:{user_id}"
    attempts = redis_client.incr(key)
    # 设置过期时间
    redis_client.expire(key, settings.LOCKOUT_DURATION_MINUTES * 60)
    return attempts


def get_login_attempts(user_id: str) -> int:
    """获取登录尝试次数"""
    key = f"login_attempts:{user_id}"
    attempts = redis_client.get(key)
    return int(attempts) if attempts else 0


def clear_login_attempts(user_id: str):
    """清除登录尝试次数"""
    key = f"login_attempts:{user_id}"
    redis_client.delete(key)


def is_account_locked(user_id: str) -> bool:
    """检查账户是否被锁定"""
    attempts = get_login_attempts(user_id)
    return attempts >= settings.MAX_LOGIN_ATTEMPTS


def validate_password_strength(password: str) -> bool:
    """验证密码强度"""
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False
    
    # 检查是否包含数字、字母和特殊字符
    has_digit = any(c.isdigit() for c in password)
    has_alpha = any(c.isalpha() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return has_digit and has_alpha and has_special 