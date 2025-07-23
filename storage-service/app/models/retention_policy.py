import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from ..db.database import Base

class RetentionPolicy(Base):
    """保留策略模型"""
    __tablename__ = "retention_policies"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    active_period = Column(Integer, nullable=False)  # 活跃期（天）
    archive_period = Column(Integer, nullable=False)  # 归档期（天）
    total_retention = Column(Integer, nullable=False)  # 总保留期（天）
    auto_delete = Column(Boolean, default=False)  # 是否自动删除
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 