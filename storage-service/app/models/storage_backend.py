import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, JSON, DateTime, BigInteger
from ..db.database import Base

class StorageBackend(Base):
    """存储后端模型"""
    __tablename__ = "storage_backends"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(50), nullable=False)  # S3, MONGODB, POSTGRESQL, FILESYSTEM
    configuration = Column(JSON, nullable=False)
    status = Column(String(50), default="active")
    priority = Column(Integer, default=1)
    capacity = Column(BigInteger, nullable=True)
    used_space = Column(BigInteger, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 