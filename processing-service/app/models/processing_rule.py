import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, JSON, DateTime, Boolean, Text
from ..db.database import Base

class ProcessingRule(Base):
    """数据处理规则模型"""
    __tablename__ = "processing_rules"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String(50), nullable=False)
    rule_definition = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 