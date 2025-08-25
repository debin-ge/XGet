from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid
from sqlalchemy import func

from ..models.user import User
from ..models.role import Role, UserRole
from ..models.session import UserSession
from ..schemas.user import UserCreate, UserUpdate, UserPasswordUpdate, UserPreferences, UserListResponse
from ..core.security import (
    get_password_hash, verify_password, create_access_token, 
    create_refresh_token, increment_login_attempts, clear_login_attempts,
    is_account_locked, validate_password_strength
)
from ..core.config import settings
from ..core.logging import logger


class UserService:
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """创建新用户"""
        # 检查用户名是否已存在
        if db.query(User).filter(User.username == user_data.username).first():
            raise ValueError("Username already exists")
        
        # 检查邮箱是否已存在
        if db.query(User).filter(User.email == user_data.email).first():
            raise ValueError("Email already exists")
        
        # 验证密码强度
        if not validate_password_strength(user_data.password):
            raise ValueError("Password does not meet strength requirements")
        
        # 创建用户
        user = User(
            id=str(uuid.uuid4()),
            username=user_data.username,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            avatar_url=user_data.avatar_url,
            timezone=user_data.timezone,
            language=user_data.language,
            preferences=UserPreferences().dict()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"Created new user: {user.username}")
        return user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        
        user = db.query(User).filter(User.id == user_id).first()

        return user
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_users(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None
    ) -> List[User]:
        """获取用户列表"""
        query = db.query(User)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if is_verified is not None:
            query = query.filter(User.is_verified == is_verified)
        
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_users_paginated(
        db: Session,
        page: int = 1,
        size: int = 20,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None
    ) -> UserListResponse:
        """获取分页用户列表（使用page/size参数，与其他服务保持一致）"""
        
        query = db.query(User)
        count_query = db.query(func.count(User.id))
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
            count_query = count_query.filter(User.is_active == is_active)
        
        if is_verified is not None:
            query = query.filter(User.is_verified == is_verified)
            count_query = count_query.filter(User.is_verified == is_verified)
        
        # 获取总数
        total = count_query.scalar() or 0
        
        # 获取分页数据
        offset = (page - 1) * size
        users = query.offset(offset).limit(size).all()
        
        # 构建响应
        response = UserListResponse.create(users, total, page, size)
        
        
        return response
    
    @staticmethod
    def update_user(db: Session, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """更新用户信息"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        # 检查用户名唯一性
        if user_data.username and user_data.username != user.username:
            existing_user = UserService.get_user_by_username(db, user_data.username)
            if existing_user:
                raise ValueError("Username already exists")
        
        # 检查邮箱唯一性
        if user_data.email and user_data.email != user.email:
            existing_user = UserService.get_user_by_email(db, user_data.email)
            if existing_user:
                raise ValueError("Email already exists")
        
        # 更新字段
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        
        logger.info(f"Updated user: {user.username}")
        return user
    
    @staticmethod
    def update_password(db: Session, user_id: str, password_data: UserPasswordUpdate) -> bool:
        """更新用户密码"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False
        
        # 验证当前密码
        if not verify_password(password_data.current_password, user.password_hash):
            raise ValueError("Current password is incorrect")
        
        # 验证新密码强度
        if not validate_password_strength(password_data.new_password):
            raise ValueError("New password does not meet strength requirements")
        
        # 更新密码
        user.password_hash = get_password_hash(password_data.new_password)
        user.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Updated password for user: {user.username}")
        return True
    
    @staticmethod
    def delete_user(db: Session, user_id: str) -> bool:
        """删除用户"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False
        
        # 软删除：设置用户为非活跃状态
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.commit()
        
        
        logger.info(f"Deleted user: {user.username}")
        return True
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """用户认证"""
        user = UserService.get_user_by_username(db, username)
        if not user:
            return None
        
        # 检查账户是否被锁定
        if is_account_locked(user.id):
            raise ValueError("Account is locked due to too many failed login attempts")
        
        # 验证密码
        if not verify_password(password, user.password_hash):
            # 增加失败登录次数
            increment_login_attempts(user.id)
            return None
        
        # 清除失败登录次数
        clear_login_attempts(user.id)
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()
        
        return user
    
    @staticmethod
    def create_user_session(
        db: Session, 
        user: User, 
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_info: Optional[str] = None
    ) -> Dict[str, str]:
        """创建用户会话"""
        # 创建访问令牌
        access_token_data = {
            "sub": user.id,
            "username": user.username,
            "email": user.email
        }
        access_token = create_access_token(access_token_data)
        
        # 创建刷新令牌
        refresh_token = create_refresh_token(access_token_data)
        
        # 保存会话到数据库
        session = UserSession(
            id=str(uuid.uuid4()),
            user_id=user.id,
            session_token=access_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
            expires_at=datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        db.add(session)
        db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "session_id": session.id
        }
    
    @staticmethod
    def revoke_session(db: Session, session_id: str) -> bool:
        """撤销用户会话"""
        session = db.query(UserSession).filter(UserSession.id == session_id).first()
        if not session:
            return False
        
        session.is_revoked = True
        session.revoked_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Revoked session: {session_id}")
        return True
    
    @staticmethod
    def get_user_roles(db: Session, user_id: str) -> List[Role]:
        """获取用户角色"""
        user_roles = db.query(UserRole).filter(
            and_(
                UserRole.user_id == user_id,
                UserRole.is_active == True,
                or_(
                    UserRole.expires_at == None,
                    UserRole.expires_at > datetime.utcnow()
                )
            )
        ).all()
        
        return [user_role.role for user_role in user_roles]
    
    @staticmethod
    def assign_role_to_user(
        db: Session, 
        user_id: str, 
        role_id: str, 
        assigned_by: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """为用户分配角色"""
        # 检查用户是否存在
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False
        
        # 检查角色是否存在
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return False
        
        # 检查是否已经分配了该角色
        existing_role = db.query(UserRole).filter(
            and_(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
                UserRole.is_active == True
            )
        ).first()
        
        if existing_role:
            return False
        
        # 分配角色
        user_role = UserRole(
            id=str(uuid.uuid4()),
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            expires_at=expires_at
        )
        
        db.add(user_role)
        db.commit()
        
        logger.info(f"Assigned role {role.name} to user {user.username}")
        return True
    
    @staticmethod
    def remove_role_from_user(db: Session, user_id: str, role_id: str) -> bool:
        """移除用户角色"""
        user_role = db.query(UserRole).filter(
            and_(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
                UserRole.is_active == True
            )
        ).first()
        
        if not user_role:
            return False
        
        user_role.is_active = False
        db.commit()
        
        logger.info(f"Removed role from user {user_id}")
        return True
    
    @staticmethod
    def update_user_preferences(db: Session, user_id: str, preferences: Dict[str, Any]) -> bool:
        """更新用户偏好设置"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False
        
        # 合并现有偏好设置
        current_preferences = user.preferences or {}
        current_preferences.update(preferences)
        user.preferences = current_preferences
        user.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Updated preferences for user: {user.username}")
        return True
    
    @staticmethod
    def verify_user_email(db: Session, user_id: str) -> bool:
        """验证用户邮箱"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False
        
        user.is_verified = True
        user.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Verified email for user: {user.username}")
        return True
    
    @staticmethod
    def initialize_admin_user(db: Session, admin_username: str = "admin", admin_password: str = "Admin123!") -> bool:
        """初始化admin用户"""
        try:
            # 检查admin用户是否已存在
            existing_admin = UserService.get_user_by_username(db, admin_username)
            if existing_admin:
                logger.info(f"Admin user '{admin_username}' already exists")
                return True
            
            # 检查admin角色是否存在
            from .role_service import RoleService
            admin_role = RoleService.get_role_by_name(db, "admin")
            if not admin_role:
                logger.error("Admin role not found. Please initialize default roles first.")
                return False
            
            # 创建admin用户
            admin_user_data = UserCreate(
                username=admin_username,
                email=f"{admin_username}@xget.com",
                password=admin_password,
                first_name="System",
                last_name="Administrator",
                timezone="UTC",
                language="en"
            )
            
            admin_user = UserService.create_user(db, admin_user_data)
            
            # 为admin用户分配admin角色
            success = UserService.assign_role_to_user(
                db=db,
                user_id=admin_user.id,
                role_id=admin_role.id,
                assigned_by="system"
            )
            
            if success:
                # 设置admin用户为已验证状态
                UserService.verify_user_email(db, admin_user.id)
                logger.info(f"Successfully initialized admin user: {admin_username}")
                return True
            else:
                logger.error(f"Failed to assign admin role to user: {admin_username}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize admin user: {str(e)}")
            db.rollback()
            return False 