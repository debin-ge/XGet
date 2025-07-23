import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..db.database import Base

class Metadata(Base):
    """元数据模型"""
    __tablename__ = "metadata"
    
    item_id = Column(String(36), ForeignKey("storage_items.id"), primary_key=True)
    source_id = Column(String(36), nullable=True, index=True)
    processing_id = Column(String(36), nullable=True, index=True)
    tags = Column(JSON, nullable=True)
    custom_fields = Column(JSON, nullable=True)
    retention_policy = Column(String(50), nullable=True)
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联存储项
    item = relationship("StorageItem", back_populates="metadata") 