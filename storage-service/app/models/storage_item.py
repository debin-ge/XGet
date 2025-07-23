import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..db.database import Base

class StorageItem(Base):
    """存储项模型"""
    __tablename__ = "storage_items"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    data_type = Column(String(50), nullable=False, index=True)
    content_hash = Column(String(255), nullable=True, index=True)
    size = Column(Integer, nullable=True)
    storage_location = Column(String(500), nullable=False)
    storage_backend = Column(String(50), nullable=False)
    compression = Column(Boolean, default=False)
    encryption = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    status = Column(String(50), default="stored")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    accessed_at = Column(DateTime, nullable=True)
    
    # 关联元数据
    metadata = relationship("Metadata", back_populates="item", uselist=False) 