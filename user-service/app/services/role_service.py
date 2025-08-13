from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from ..models.role import Role, Permission, UserRole
from ..schemas.role import RoleCreate, RoleUpdate, PermissionCreate
from ..core.logging import logger


class RoleService:
    
    @staticmethod
    def create_role(db: Session, role_data: RoleCreate) -> Role:
        """创建新角色"""
        # 检查角色名是否已存在
        if db.query(Role).filter(Role.name == role_data.name).first():
            raise ValueError("Role name already exists")
        
        # 创建角色
        role = Role(
            id=str(uuid.uuid4()),
            name=role_data.name,
            description=role_data.description
        )
        
        db.add(role)
        db.commit()
        db.refresh(role)
        
        # 分配权限
        if role_data.permission_ids:
            RoleService.assign_permissions_to_role(db, role.id, role_data.permission_ids)
        
        logger.info(f"Created new role: {role.name}")
        return role
    
    @staticmethod
    def get_role_by_id(db: Session, role_id: str) -> Optional[Role]:
        """根据ID获取角色"""
        return db.query(Role).filter(Role.id == role_id).first()
    
    @staticmethod
    def get_role_by_name(db: Session, name: str) -> Optional[Role]:
        """根据名称获取角色"""
        return db.query(Role).filter(Role.name == name).first()
    
    @staticmethod
    def get_roles(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Role]:
        """获取角色列表"""
        query = db.query(Role)
        
        if is_active is not None:
            query = query.filter(Role.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_role(db: Session, role_id: str, role_data: RoleUpdate) -> Optional[Role]:
        """更新角色"""
        role = RoleService.get_role_by_id(db, role_id)
        if not role:
            return None
        
        # 检查角色名唯一性
        if role_data.name and role_data.name != role.name:
            existing_role = RoleService.get_role_by_name(db, role_data.name)
            if existing_role:
                raise ValueError("Role name already exists")
        
        # 更新字段
        update_data = role_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field != "permission_ids":
                setattr(role, field, value)
        
        role.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(role)
        
        # 更新权限
        if role_data.permission_ids is not None:
            RoleService.update_role_permissions(db, role_id, role_data.permission_ids)
        
        logger.info(f"Updated role: {role.name}")
        return role
    
    @staticmethod
    def delete_role(db: Session, role_id: str) -> bool:
        """删除角色"""
        role = RoleService.get_role_by_id(db, role_id)
        if not role:
            return False
        
        # 检查是否有用户使用该角色
        user_roles = db.query(UserRole).filter(
            and_(
                UserRole.role_id == role_id,
                UserRole.is_active == True
            )
        ).count()
        
        if user_roles > 0:
            raise ValueError("Cannot delete role that is assigned to users")
        
        # 软删除
        role.is_active = False
        role.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Deleted role: {role.name}")
        return True
    
    @staticmethod
    def create_permission(db: Session, permission_data: PermissionCreate) -> Permission:
        """创建新权限"""
        # 检查权限名是否已存在
        if db.query(Permission).filter(Permission.name == permission_data.name).first():
            raise ValueError("Permission name already exists")
        
        # 创建权限
        permission = Permission(
            id=str(uuid.uuid4()),
            name=permission_data.name,
            description=permission_data.description,
            resource=permission_data.resource,
            action=permission_data.action
        )
        
        db.add(permission)
        db.commit()
        db.refresh(permission)
        
        logger.info(f"Created new permission: {permission.name}")
        return permission
    
    @staticmethod
    def get_permission_by_id(db: Session, permission_id: str) -> Optional[Permission]:
        """根据ID获取权限"""
        return db.query(Permission).filter(Permission.id == permission_id).first()
    
    @staticmethod
    def get_permissions(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        resource: Optional[str] = None,
        action: Optional[str] = None
    ) -> List[Permission]:
        """获取权限列表"""
        query = db.query(Permission)
        
        if resource:
            query = query.filter(Permission.resource == resource)
        
        if action:
            query = query.filter(Permission.action == action)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def assign_permissions_to_role(db: Session, role_id: str, permission_ids: List[str]) -> bool:
        """为角色分配权限"""
        role = RoleService.get_role_by_id(db, role_id)
        if not role:
            return False
        
        # 获取权限
        permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        
        # 分配权限
        role.permissions = permissions
        db.commit()
        
        logger.info(f"Assigned {len(permissions)} permissions to role {role.name}")
        return True
    
    @staticmethod
    def update_role_permissions(db: Session, role_id: str, permission_ids: List[str]) -> bool:
        """更新角色权限"""
        return RoleService.assign_permissions_to_role(db, role_id, permission_ids)
    
    @staticmethod
    def get_role_permissions(db: Session, role_id: str) -> List[Permission]:
        """获取角色权限"""
        role = RoleService.get_role_by_id(db, role_id)
        if not role:
            return []
        
        return role.permissions
    
    @staticmethod
    def get_user_permissions(db: Session, user_id: str) -> List[Permission]:
        """获取用户所有权限"""
        user_roles = db.query(UserRole).filter(
            and_(
                UserRole.user_id == user_id,
                UserRole.is_active == True
            )
        ).all()
        
        permissions = set()
        for user_role in user_roles:
            for permission in user_role.role.permissions:
                permissions.add(permission)
        
        return list(permissions)
    
    @staticmethod
    def check_user_permission(db: Session, user_id: str, resource: str, action: str) -> bool:
        """检查用户是否有特定权限"""
        permissions = RoleService.get_user_permissions(db, user_id)
        
        for permission in permissions:
            if permission.resource == resource and permission.action == action:
                return True
        
        return False
    
    @staticmethod
    def get_permissions_by_resource(db: Session, resource: str) -> List[Permission]:
        """根据资源获取权限"""
        return db.query(Permission).filter(Permission.resource == resource).all()
    
    @staticmethod
    def get_default_roles() -> List[Dict[str, Any]]:
        """获取默认角色定义"""
        return [
            {
                "name": "admin",
                "description": "System administrator with full access",
                "permissions": [
                    {"resource": "user", "action": "create"},
                    {"resource": "user", "action": "read"},
                    {"resource": "user", "action": "update"},
                    {"resource": "user", "action": "delete"},
                    {"resource": "role", "action": "create"},
                    {"resource": "role", "action": "read"},
                    {"resource": "role", "action": "update"},
                    {"resource": "role", "action": "delete"},
                    {"resource": "account", "action": "create"},
                    {"resource": "account", "action": "read"},
                    {"resource": "account", "action": "update"},
                    {"resource": "account", "action": "delete"},
                    {"resource": "proxy", "action": "create"},
                    {"resource": "proxy", "action": "read"},
                    {"resource": "proxy", "action": "update"},
                    {"resource": "proxy", "action": "delete"},
                ]
            },
            {
                "name": "user",
                "description": "Regular user with basic access",
                "permissions": [
                    {"resource": "user", "action": "read"},
                    {"resource": "user", "action": "update"},
                    {"resource": "account", "action": "read"},
                    {"resource": "account", "action": "create"},
                    {"resource": "account", "action": "update"},
                    {"resource": "proxy", "action": "read"},
                ]
            },
            {
                "name": "guest",
                "description": "Guest user with limited access",
                "permissions": [
                    {"resource": "user", "action": "read"},
                    {"resource": "account", "action": "read"},
                ]
            }
        ]
    
    @staticmethod
    def initialize_default_roles(db: Session) -> bool:
        """初始化默认角色"""
        try:
            default_roles = RoleService.get_default_roles()
            
            for role_data in default_roles:
                # 检查角色是否已存在
                existing_role = RoleService.get_role_by_name(db, role_data["name"])
                if existing_role:
                    continue
                
                # 创建权限
                permission_ids = []
                for perm_data in role_data["permissions"]:
                    permission = db.query(Permission).filter(
                        and_(
                            Permission.resource == perm_data["resource"],
                            Permission.action == perm_data["action"]
                        )
                    ).first()
                    
                    if not permission:
                        permission = RoleService.create_permission(db, PermissionCreate(
                            name=f"{perm_data['resource']}_{perm_data['action']}",
                            description=f"Can {perm_data['action']} {perm_data['resource']}",
                            resource=perm_data["resource"],
                            action=perm_data["action"]
                        ))
                    
                    permission_ids.append(permission.id)
                
                # 创建角色
                role = RoleService.create_role(db, RoleCreate(
                    name=role_data["name"],
                    description=role_data["description"],
                    permission_ids=permission_ids
                ))
            
            logger.info("Initialized default roles successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize default roles: {e}")
            return False 