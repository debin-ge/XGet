from sqlalchemy import Column, String, Boolean, DateTime, JSON, func
from ..db.database import Base
import uuid


class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    password = Column(String)
    email = Column(String)
    email_password = Column(String)
    login_method = Column(String)
    proxy_id = Column(String, nullable=True)
    cookies = Column(JSON, nullable=True)
    headers = Column(JSON, nullable=True)
    user_agent = Column(String, nullable=True)
    active = Column(Boolean, default=False)
    last_used = Column(DateTime, nullable=True)
    error_msg = Column(String, nullable=True)
    
    # 软删除字段
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
